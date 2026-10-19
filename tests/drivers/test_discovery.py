from __future__ import annotations

from collections.abc import Iterable, MutableMapping
from importlib import metadata
from typing import cast

import pytest

from ovcaq.drivers.base import (
    DRIVER_API_VERSION,
    AgentDriver,
    DriverDiscoveryError,
    DriverFactory,
    DriverHealth,
    DriverPlugin,
    DuplicateDriverError,
    IncompatibleDriverError,
    LaunchRequest,
    LaunchSpec,
    discover_drivers,
)
from ovcaq.events import Observation, SessionSummary, reduce_session


class RegistryDriver:
    def default_prompt(self, phase: str) -> str:
        return f"Run {phase}"

    def __init__(
        self,
        name: str,
        events: list[str],
        health: DriverHealth,
        probe_error: Exception | None,
    ) -> None:
        self.name = name
        self.events = events
        self.health = health
        self.probe_error = probe_error

    def probe(self) -> DriverHealth:
        self.events.append(f"probe:{self.name}")
        if self.probe_error is not None:
            raise self.probe_error
        return self.health

    def build_launch(self, request: LaunchRequest) -> LaunchSpec:
        return LaunchSpec(("sample-agent", request.prompt), {}, request.root, "text")

    def decode(self, raw_line: str) -> Iterable[Observation]:
        return ()

    def summarize(
        self, observations: Iterable[Observation], exit_code: int
    ) -> SessionSummary:
        return reduce_session(observations, exit_code).summary


def plugin(
    name: str,
    events: list[str],
    *,
    version: int = DRIVER_API_VERSION,
    health: DriverHealth | None = None,
    factory_error: Exception | None = None,
    probe_error: Exception | None = None,
) -> DriverPlugin:
    def create() -> AgentDriver:
        events.append(f"factory:{name}")
        if factory_error is not None:
            raise factory_error
        return RegistryDriver(
            name,
            events,
            DriverHealth(True, "ready") if health is None else health,
            probe_error,
        )

    factory: DriverFactory = create
    return DriverPlugin(version, factory)


class EntryCatalog:
    def __init__(self) -> None:
        self.objects: dict[metadata.EntryPoint, object] = {}
        self.events: list[str] = []

    def add(self, name: str, loaded: object) -> metadata.EntryPoint:
        entry_point = metadata.EntryPoint(
            name=name,
            value=f"sample_distribution:plugin_{len(self.objects)}",
            group="ovcaq.drivers",
        )
        self.objects[entry_point] = loaded
        return entry_point

    def load(self, entry_point: metadata.EntryPoint) -> object:
        self.events.append(f"load:{entry_point.name}")
        loaded = self.objects[entry_point]
        if isinstance(loaded, Exception):
            raise loaded
        return loaded


@pytest.fixture
def catalog(monkeypatch: pytest.MonkeyPatch) -> EntryCatalog:
    result = EntryCatalog()

    def load(entry_point: metadata.EntryPoint) -> object:
        return result.load(entry_point)

    monkeypatch.setattr(metadata.EntryPoint, "load", load)
    return result


def test_empty_discovery_returns_an_empty_read_only_mapping() -> None:
    discovered = discover_drivers((), entry_points=())

    assert dict(discovered) == {}
    with pytest.raises(TypeError):
        cast(MutableMapping[str, AgentDriver], discovered)["new"] = RegistryDriver(
            "new", [], DriverHealth(True, "ready"), None
        )


def test_discovery_preserves_builtin_order_and_sorts_entry_points(
    catalog: EntryCatalog,
) -> None:
    events = catalog.events
    builtins = (plugin("zulu", events), plugin("alpha", events))
    third_party = (
        catalog.add("tango", plugin("tango", events)),
        catalog.add("beta", plugin("beta", events)),
    )

    discovered = discover_drivers(iter(builtins), entry_points=iter(third_party))

    assert tuple(discovered) == ("zulu", "alpha", "beta", "tango")
    assert tuple(driver.name for driver in discovered.values()) == tuple(discovered)
    assert events == [
        "factory:zulu",
        "probe:zulu",
        "factory:alpha",
        "probe:alpha",
        "load:beta",
        "factory:beta",
        "probe:beta",
        "load:tango",
        "factory:tango",
        "probe:tango",
    ]


def test_discovery_returns_the_exact_once_constructed_and_probed_driver() -> None:
    events: list[str] = []
    driver = RegistryDriver("sample", events, DriverHealth(True, "ready"), None)

    def create() -> AgentDriver:
        events.append("factory:sample")
        return driver

    discovered = discover_drivers((DriverPlugin(2, create),), entry_points=())

    assert discovered["sample"] is driver
    assert events == ["factory:sample", "probe:sample"]
    with pytest.raises(TypeError):
        del cast(MutableMapping[str, AgentDriver], discovered)["sample"]
    assert discovered["sample"] is driver


def test_default_discovery_queries_only_the_declared_entry_point_group(
    catalog: EntryCatalog, monkeypatch: pytest.MonkeyPatch
) -> None:
    entry_point = catalog.add("sample", plugin("sample", catalog.events))
    groups: list[str] = []

    def entry_points(*, group: str) -> tuple[metadata.EntryPoint, ...]:
        groups.append(group)
        return (entry_point,)

    monkeypatch.setattr(metadata, "entry_points", entry_points)

    discovered = discover_drivers(())

    assert groups == ["ovcaq.drivers"]
    assert tuple(discovered) == ("sample",)
    assert catalog.events == ["load:sample", "factory:sample", "probe:sample"]


def test_supplied_entry_points_do_not_query_the_installed_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def entry_points(*, group: str) -> tuple[metadata.EntryPoint, ...]:
        raise AssertionError(f"Unexpected environment discovery for {group}")

    monkeypatch.setattr(metadata, "entry_points", entry_points)
    assert dict(discover_drivers((), entry_points=())) == {}


@pytest.mark.parametrize("version", (-1, 0, 1, 99))
@pytest.mark.parametrize("source", ("builtin", "entry-point"))
def test_incompatible_versions_fail_before_factory_construction(
    catalog: EntryCatalog, version: int, source: str
) -> None:
    candidate = plugin("sample", catalog.events, version=version)
    builtins = (candidate,) if source == "builtin" else ()
    entries = (catalog.add("sample", candidate),) if source == "entry-point" else ()

    with pytest.raises(IncompatibleDriverError) as caught:
        discover_drivers(builtins, entry_points=entries)

    assert isinstance(caught.value, DriverDiscoveryError)
    assert str(DRIVER_API_VERSION) in str(caught.value)
    assert str(version) in str(caught.value)
    assert "factory:sample" not in catalog.events


@pytest.mark.parametrize("source", ("builtins", "entry-points", "mixed"))
@pytest.mark.parametrize("reuse_plugin", (True, False), ids=("same", "distinct"))
def test_duplicate_names_are_rejected_with_no_replacement(
    catalog: EntryCatalog, source: str, reuse_plugin: bool
) -> None:
    candidate = plugin("sample", catalog.events)
    duplicate = candidate if reuse_plugin else plugin("sample", catalog.events)
    entry_point = catalog.add("sample", candidate)
    duplicate_entry = entry_point if reuse_plugin else catalog.add("sample", duplicate)
    sources = {
        "builtins": ((candidate, duplicate), ()),
        "entry-points": ((), (entry_point, duplicate_entry)),
        "mixed": ((candidate,), (duplicate_entry,)),
    }
    builtins, entries = sources[source]

    with pytest.raises(DuplicateDriverError) as caught:
        discover_drivers(builtins, entry_points=entries)

    assert isinstance(caught.value, DriverDiscoveryError)
    assert "sample" in str(caught.value)


@pytest.mark.parametrize("source", ("builtin", "entry-point"))
@pytest.mark.parametrize("loaded", (None, 1, "sample"))
def test_discovery_rejects_sources_that_are_not_plugin_records(
    catalog: EntryCatalog, source: str, loaded: object
) -> None:
    builtins = (cast(DriverPlugin, loaded),) if source == "builtin" else ()
    entries = (catalog.add("sample", loaded),) if source == "entry-point" else ()

    with pytest.raises(DriverDiscoveryError):
        discover_drivers(builtins, entry_points=entries)


def test_entry_point_must_load_a_plugin_and_cannot_load_a_bare_factory(
    catalog: EntryCatalog,
) -> None:
    candidate = plugin("sample", catalog.events)
    entry_point = catalog.add("sample", candidate.factory)

    with pytest.raises(DriverDiscoveryError) as caught:
        discover_drivers((), entry_points=(entry_point,))

    assert "sample" in str(caught.value)
    assert catalog.events == ["load:sample"]


def test_entry_point_load_failure_identifies_source_and_retains_cause(
    catalog: EntryCatalog,
) -> None:
    original = ImportError("sample dependency unavailable")
    entry_point = catalog.add("sample", original)

    with pytest.raises(DriverDiscoveryError) as caught:
        discover_drivers((), entry_points=(entry_point,))

    assert "sample" in str(caught.value)
    assert caught.value.__cause__ is original
    assert catalog.events == ["load:sample"]


@pytest.mark.parametrize("source", ("builtin", "entry-point"))
def test_factory_failure_identifies_source_and_retains_cause(
    catalog: EntryCatalog, source: str
) -> None:
    original = RuntimeError("sample factory failed")
    candidate = plugin("sample", catalog.events, factory_error=original)
    builtins = (candidate,) if source == "builtin" else ()
    entries = (catalog.add("sample", candidate),) if source == "entry-point" else ()

    with pytest.raises(DriverDiscoveryError) as caught:
        discover_drivers(builtins, entry_points=entries)

    assert "sample" in str(caught.value)
    assert caught.value.__cause__ is original
    assert catalog.events.count("factory:sample") == 1
    assert "probe:sample" not in catalog.events


@pytest.mark.parametrize("name", ("", None, 1))
def test_entry_point_rejects_invalid_driver_name_with_source_diagnostic(
    catalog: EntryCatalog, name: object
) -> None:
    entry_point = catalog.add("sample", plugin(cast(str, name), catalog.events))

    with pytest.raises(DriverDiscoveryError) as caught:
        discover_drivers((), entry_points=(entry_point,))

    assert "sample" in str(caught.value)


@pytest.mark.parametrize("name", ("", None, 1))
def test_builtin_rejects_invalid_driver_name(name: object) -> None:
    candidate = plugin(cast(str, name), [])

    with pytest.raises(DriverDiscoveryError):
        discover_drivers((candidate,), entry_points=())


def test_entry_point_name_must_match_the_driver_name(catalog: EntryCatalog) -> None:
    entry_point = catalog.add("advertised", plugin("actual", catalog.events))

    with pytest.raises(DriverDiscoveryError) as caught:
        discover_drivers((), entry_points=(entry_point,))

    assert "advertised" in str(caught.value)
    assert "actual" in str(caught.value)


@pytest.mark.parametrize("source", ("builtin", "entry-point"))
def test_probe_failure_identifies_driver_and_retains_cause(
    catalog: EntryCatalog, source: str
) -> None:
    original = OSError("sample executable unavailable")
    candidate = plugin("sample", catalog.events, probe_error=original)
    builtins = (candidate,) if source == "builtin" else ()
    entries = (catalog.add("sample", candidate),) if source == "entry-point" else ()

    with pytest.raises(DriverDiscoveryError) as caught:
        discover_drivers(builtins, entry_points=entries)

    assert "sample" in str(caught.value)
    assert caught.value.__cause__ is original
    assert catalog.events.count("factory:sample") == 1
    assert catalog.events.count("probe:sample") == 1


@pytest.mark.parametrize("source", ("builtin", "entry-point"))
@pytest.mark.parametrize("name", ("unavailable", "sample"))
def test_unhealthy_probe_fails_closed_after_an_earlier_healthy_driver(
    catalog: EntryCatalog, source: str, name: str
) -> None:
    healthy = plugin("ready", catalog.events)
    unhealthy = plugin(
        name, catalog.events, health=DriverHealth(False, "missing executable")
    )
    builtins = (healthy, unhealthy) if source == "builtin" else (healthy,)
    entries = (catalog.add(name, unhealthy),) if source == "entry-point" else ()

    with pytest.raises(DriverDiscoveryError) as caught:
        discover_drivers(builtins, entry_points=entries)

    assert name in str(caught.value)
    assert catalog.events.count("factory:ready") == 1
    assert catalog.events.count("probe:ready") == 1
    assert catalog.events.count(f"factory:{name}") == 1
    assert catalog.events.count(f"probe:{name}") == 1


@pytest.mark.parametrize("source", ("builtin", "entry-point"))
def test_healthy_driver_named_unavailable_is_discovered(
    catalog: EntryCatalog, source: str
) -> None:
    candidate = plugin(
        "unavailable", catalog.events, health=DriverHealth(True, "ready")
    )
    builtins = (candidate,) if source == "builtin" else ()
    entries = (
        (catalog.add("unavailable", candidate),) if source == "entry-point" else ()
    )

    discovered = discover_drivers(builtins, entry_points=entries)

    assert tuple(discovered) == ("unavailable",)
    assert discovered["unavailable"].name == "unavailable"
    assert catalog.events.count("factory:unavailable") == 1
    assert catalog.events.count("probe:unavailable") == 1
