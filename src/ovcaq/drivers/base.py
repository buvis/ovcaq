"""Provider-neutral driver records, protocol, and plugin discovery."""

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from types import MappingProxyType
from typing import Protocol

from ovcaq.events import Observation, SessionSummary

DRIVER_API_VERSION = 2


def _require_string(value: object, field: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value:
        raise ValueError(f"{field} must not be empty")


@dataclass(frozen=True, slots=True)
class LaunchRequest:
    root: Path
    phase: str
    prompt: str
    model: str | None
    effort: str | None
    timeout_seconds: int
    session_dir: Path

    def __post_init__(self) -> None:
        for field in ("root", "session_dir"):
            if not isinstance(getattr(self, field), Path):
                raise TypeError(f"{field} must be a Path")
        for field in ("phase", "prompt"):
            _require_string(getattr(self, field), field)
        for field in ("model", "effort"):
            value = getattr(self, field)
            if value is not None:
                _require_string(value, field)
        if type(self.timeout_seconds) is not int:
            raise TypeError("timeout_seconds must be an integer")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


@dataclass(frozen=True, slots=True)
class LaunchSpec:
    argv: tuple[str, ...]
    env: Mapping[str, str]
    cwd: Path
    raw_format: str

    def __post_init__(self) -> None:
        if not isinstance(self.argv, tuple):
            raise TypeError("argv must be a tuple")
        if not self.argv:
            raise ValueError("argv must not be empty")
        for argument in self.argv:
            _require_string(argument, "argv argument")
        if not isinstance(self.env, Mapping):
            raise TypeError("env must be a mapping")
        for key, value in self.env.items():
            _require_string(key, "env key")
            _require_string(value, "env value")
        object.__setattr__(self, "env", MappingProxyType(dict(self.env)))
        if not isinstance(self.cwd, Path):
            raise TypeError("cwd must be a Path")
        _require_string(self.raw_format, "raw_format")


@dataclass(frozen=True, slots=True)
class DriverHealth:
    healthy: bool
    detail: str

    def __post_init__(self) -> None:
        if type(self.healthy) is not bool:
            raise TypeError("healthy must be a boolean")
        if not isinstance(self.detail, str):
            raise TypeError("detail must be a string")


class AgentDriver(Protocol):
    name: str
    default_tiers: Mapping[str, str]

    def default_prompt(self, phase: str) -> str: ...

    def probe(self) -> DriverHealth: ...

    def build_launch(self, request: LaunchRequest) -> LaunchSpec: ...

    def decode(self, raw_line: str) -> Iterable[Observation]: ...

    def summarize(
        self, observations: Iterable[Observation], exit_code: int
    ) -> SessionSummary: ...


DriverFactory = Callable[[], AgentDriver]


@dataclass(frozen=True, slots=True)
class DriverPlugin:
    api_version: int
    factory: DriverFactory

    def __post_init__(self) -> None:
        if type(self.api_version) is not int:
            raise TypeError("api_version must be an integer")
        if not callable(self.factory):
            raise TypeError("factory must be callable")


class DriverDiscoveryError(RuntimeError):
    """A driver could not be loaded, constructed, or verified."""


class IncompatibleDriverError(DriverDiscoveryError):
    """A plugin declares an unsupported driver API version."""


class DuplicateDriverError(DriverDiscoveryError):
    """More than one plugin declares the same driver name."""


def _register_driver(
    discovered: dict[str, AgentDriver],
    candidate: object,
    source: str,
    advertised_name: str | None = None,
) -> None:
    if not isinstance(candidate, DriverPlugin):
        raise DriverDiscoveryError(f"{source} must provide a DriverPlugin")
    if candidate.api_version != DRIVER_API_VERSION:
        raise IncompatibleDriverError(
            f"{source} uses driver API {candidate.api_version}; "
            f"expected {DRIVER_API_VERSION}"
        )
    try:
        driver = candidate.factory()
    except Exception as exc:
        raise DriverDiscoveryError(f"{source} factory failed: {exc}") from exc
    name = driver.name
    if not isinstance(name, str) or not name:
        raise DriverDiscoveryError(f"{source} has an invalid driver name: {name!r}")
    if advertised_name is not None and name != advertised_name:
        raise DriverDiscoveryError(
            f"{source} advertises {advertised_name!r} but returned {name!r}"
        )
    if name in discovered:
        raise DuplicateDriverError(f"Duplicate driver name: {name!r} ({source})")
    try:
        health = driver.probe()
    except Exception as exc:
        raise DriverDiscoveryError(
            f"Driver {name!r} from {source} probe failed: {exc}"
        ) from exc
    if not health.healthy:
        raise DriverDiscoveryError(
            f"Driver {name!r} from {source} is unhealthy: {health.detail}"
        )
    discovered[name] = driver


def discover_drivers(
    builtins: Iterable[DriverPlugin],
    *,
    entry_points: Iterable[metadata.EntryPoint] | None = None,
) -> Mapping[str, AgentDriver]:
    """Construct and probe each plugin, returning an immutable ordered registry."""
    discovered: dict[str, AgentDriver] = {}
    for index, candidate in enumerate(builtins):
        _register_driver(discovered, candidate, f"builtin {index}")
    if entry_points is None:
        entry_points = metadata.entry_points(group="ovcaq.drivers")
    for entry_point in sorted(entry_points, key=lambda entry: entry.name):
        source = f"entry point {entry_point.name!r}"
        try:
            loaded = entry_point.load()
        except Exception as exc:
            raise DriverDiscoveryError(f"Could not load {source}: {exc}") from exc
        _register_driver(discovered, loaded, source, entry_point.name)
    return MappingProxyType(discovered)
