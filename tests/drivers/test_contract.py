from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, MutableMapping
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pytest

from ovcaq import drivers
from ovcaq.drivers import base
from ovcaq.drivers.base import (
    DRIVER_API_VERSION,
    AgentDriver,
    DriverFactory,
    DriverHealth,
    DriverPlugin,
    LaunchRequest,
    LaunchSpec,
)
from ovcaq.events import (
    PROTOCOL_VERSION,
    Observation,
    ObservationType,
    SessionSummary,
    observation_record,
    reduce_session,
)


class FakeDriver:
    name = "sample"

    def default_prompt(self, phase: str) -> str:
        return f"Run {phase}"

    def probe(self) -> DriverHealth:
        return DriverHealth(healthy=True, detail="available")

    def build_launch(self, request: LaunchRequest) -> LaunchSpec:
        return LaunchSpec(
            argv=("sample-agent", "--prompt", request.prompt),
            env={"RUN_PHASE": request.phase},
            cwd=request.root,
            raw_format="text",
        )

    def decode(self, raw_line: str) -> Iterable[Observation]:
        kind = ObservationType.RAW_UNKNOWN
        payload = {
            "reason": "unrecognized input",
            "raw_sha256": hashlib.sha256(raw_line.encode()).hexdigest(),
            "preview": raw_line,
        }
        if raw_line == "done":
            kind = ObservationType.SESSION_COMPLETED
            payload = {}
        return (
            Observation(
                protocol_version=PROTOCOL_VERSION,
                timestamp=datetime(2026, 1, 1, tzinfo=UTC),
                provider=self.name,
                run_id="sample-run",
                session_id="sample-session",
                lane_id=None,
                type=kind,
                payload=payload,
            ),
        )

    def summarize(
        self, observations: Iterable[Observation], exit_code: int
    ) -> SessionSummary:
        return reduce_session(observations, exit_code).summary


@pytest.fixture
def request_record(tmp_path: Path) -> LaunchRequest:
    return LaunchRequest(
        root=tmp_path,
        phase="build",
        prompt="Keep this prompt literal; $(anything) | anything",
        model=None,
        effort=None,
        timeout_seconds=1,
        session_dir=tmp_path / "session",
    )


@pytest.fixture
def launch_spec(tmp_path: Path) -> LaunchSpec:
    return LaunchSpec(
        argv=("sample-agent", "--prompt", "literal text"),
        env={"RUN_PHASE": "build"},
        cwd=tmp_path,
        raw_format="text",
    )


@pytest.mark.parametrize(
    "name",
    (
        "DRIVER_API_VERSION",
        "LaunchRequest",
        "LaunchSpec",
        "DriverHealth",
        "AgentDriver",
        "DriverFactory",
        "DriverPlugin",
        "DriverDiscoveryError",
        "IncompatibleDriverError",
        "DuplicateDriverError",
        "discover_drivers",
    ),
)
def test_package_exports_the_same_public_driver_contract(name: str) -> None:
    assert getattr(drivers, name) is getattr(base, name)


def test_driver_api_version_is_integer_two() -> None:
    assert type(DRIVER_API_VERSION) is int
    assert DRIVER_API_VERSION == 2


@pytest.mark.parametrize("timeout_seconds", (1, 37))
def test_launch_request_preserves_inputs_and_optional_strings(
    request_record: LaunchRequest, tmp_path: Path, timeout_seconds: int
) -> None:
    request_record = replace(request_record, timeout_seconds=timeout_seconds)
    assert request_record.root == tmp_path
    assert request_record.session_dir == tmp_path / "session"
    assert request_record.phase == "build"
    assert request_record.prompt == "Keep this prompt literal; $(anything) | anything"
    assert request_record.timeout_seconds == timeout_seconds
    assert request_record.model is None
    assert request_record.effort is None
    specified = replace(request_record, model="sample-model", effort="sample-effort")
    assert specified.model == "sample-model"
    assert specified.effort == "sample-effort"


@pytest.mark.parametrize(
    ("field", "value", "error"),
    (
        ("root", "/workspace", TypeError),
        ("root", None, TypeError),
        ("session_dir", "/session", TypeError),
        ("session_dir", None, TypeError),
        ("phase", "", ValueError),
        ("phase", None, TypeError),
        ("phase", 1, TypeError),
        ("prompt", "", ValueError),
        ("prompt", None, TypeError),
        ("prompt", 1, TypeError),
        ("model", "", ValueError),
        ("model", 1, TypeError),
        ("effort", "", ValueError),
        ("effort", 1, TypeError),
        ("timeout_seconds", 0, ValueError),
        ("timeout_seconds", -1, ValueError),
        ("timeout_seconds", True, TypeError),
        ("timeout_seconds", False, TypeError),
        ("timeout_seconds", 1.0, TypeError),
        ("timeout_seconds", None, TypeError),
    ),
)
def test_launch_request_rejects_invalid_fields(
    request_record: LaunchRequest, field: str, value: object, error: type[Exception]
) -> None:
    with pytest.raises(error):
        replace(request_record, **{field: value})


@pytest.mark.parametrize(
    ("field", "value", "error"),
    (
        pytest.param(
            "argv", "sample-agent --prompt text", TypeError, id="shell-string"
        ),
        pytest.param("argv", ["sample-agent"], TypeError, id="list-argv"),
        pytest.param("argv", (), ValueError, id="empty-argv"),
        pytest.param("argv", ("sample-agent", ""), ValueError, id="empty-argument"),
        pytest.param("argv", ("sample-agent", 1), TypeError, id="nonstring-argument"),
        pytest.param("env", None, TypeError, id="missing-env"),
        pytest.param("env", [("KEY", "value")], TypeError, id="nonmapping-env"),
        pytest.param("env", {"": "value"}, ValueError, id="empty-env-key"),
        pytest.param("env", {"KEY": ""}, ValueError, id="empty-env-value"),
        pytest.param("env", {1: "value"}, TypeError, id="nonstring-env-key"),
        pytest.param("env", {"KEY": None}, TypeError, id="nonstring-env-value"),
        pytest.param("cwd", "/workspace", TypeError, id="string-cwd"),
        pytest.param("cwd", None, TypeError, id="missing-cwd"),
        pytest.param("raw_format", "", ValueError, id="empty-format"),
        pytest.param("raw_format", None, TypeError, id="missing-format"),
    ),
)
def test_launch_spec_rejects_invalid_fields(
    launch_spec: LaunchSpec, field: str, value: object, error: type[Exception]
) -> None:
    with pytest.raises(error):
        replace(launch_spec, **{field: value})


@pytest.mark.parametrize("raw_format", ("text", "jsonl"))
def test_launch_spec_preserves_the_requested_raw_format(
    launch_spec: LaunchSpec, raw_format: str
) -> None:
    spec = replace(launch_spec, raw_format=raw_format)

    assert spec.raw_format == raw_format


def test_launch_spec_copies_and_freezes_environment(launch_spec: LaunchSpec) -> None:
    environment = {"RUN_PHASE": "build"}
    spec = replace(launch_spec, env=environment)
    environment["RUN_PHASE"] = "review"
    environment["NEW_KEY"] = "new value"

    assert dict(spec.env) == {"RUN_PHASE": "build"}
    with pytest.raises(TypeError):
        cast(MutableMapping[str, str], spec.env)["RUN_PHASE"] = "review"
    assert dict(replace(launch_spec, env={}).env) == {}


@pytest.mark.parametrize(
    ("field", "value"),
    (("healthy", 1), ("healthy", "yes"), ("healthy", None), ("detail", None)),
)
def test_driver_health_rejects_wrong_field_types(field: str, value: object) -> None:
    with pytest.raises(TypeError):
        replace(DriverHealth(True, ""), **{field: value})


def test_driver_health_accepts_both_boolean_states_and_empty_detail() -> None:
    assert DriverHealth(True, "").healthy is True
    assert DriverHealth(False, "").healthy is False
    assert DriverHealth(False, "").detail == ""


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("api_version", True),
        ("api_version", 1.0),
        ("api_version", "1"),
        ("api_version", None),
        ("factory", None),
        ("factory", "sample"),
    ),
)
def test_plugin_rejects_wrong_field_types(field: str, value: object) -> None:
    with pytest.raises(TypeError):
        replace(DriverPlugin(DRIVER_API_VERSION, FakeDriver), **{field: value})


@pytest.mark.parametrize("version", (-1, 0, 1, 2))
def test_plugin_retains_integer_version_for_discovery_to_check(version: int) -> None:
    factory: DriverFactory = FakeDriver
    plugin = DriverPlugin(version, factory)
    assert plugin.api_version == version
    assert plugin.factory is factory


@pytest.mark.parametrize("record_kind", ("request", "launch", "health", "plugin"))
def test_driver_records_are_frozen_and_slotted(
    request_record: LaunchRequest, launch_spec: LaunchSpec, record_kind: str
) -> None:
    records = {
        "request": (request_record, "phase", "review"),
        "launch": (launch_spec, "raw_format", "jsonl"),
        "health": (DriverHealth(True, "ready"), "healthy", False),
        "plugin": (DriverPlugin(1, FakeDriver), "api_version", 2),
    }
    record, field, value = records[record_kind]
    assert not hasattr(record, "__dict__")
    with pytest.raises(FrozenInstanceError):
        setattr(record, field, value)


def test_fake_driver_runs_through_the_protocol(request_record: LaunchRequest) -> None:
    driver: AgentDriver = FakeDriver()
    spec = driver.build_launch(request_record)
    observations = tuple(driver.decode("done"))
    summary = driver.summarize(iter(observations), 0)

    assert driver.name == "sample"
    assert driver.probe() == DriverHealth(True, "available")
    assert spec.argv == ("sample-agent", "--prompt", request_record.prompt)
    assert spec.cwd == request_record.root
    assert dict(spec.env) == {"RUN_PHASE": "build"}
    assert spec.raw_format == "text"
    assert observations[0].type == ObservationType.SESSION_COMPLETED
    assert summary == SessionSummary(
        success=True,
        session_id="sample-session",
        failure_class=None,
        failure_detail=None,
        rate_limit_reset_at=None,
        usage=None,
    )
    assert isinstance(summary, SessionSummary)
    assert summary.success is True
    assert summary.session_id == "sample-session"


@pytest.mark.parametrize("raw_line", ("", "{broken", "null", "[]", "λ🙂", "x" * 2048))
def test_fake_decoder_is_total_and_returns_normalized_evidence(raw_line: str) -> None:
    driver: AgentDriver = FakeDriver()
    observations = tuple(driver.decode(raw_line))

    assert len(observations) == 1
    observation = observations[0]
    assert isinstance(observation, Observation)
    assert observation.type == ObservationType.RAW_UNKNOWN
    assert observation.provider == "sample"
    assert observation.run_id == "sample-run"
    assert (
        observation.payload["raw_sha256"]
        == hashlib.sha256(raw_line.encode()).hexdigest()
    )
    assert observation.payload["preview"] == raw_line[:512]
    assert json.loads(json.dumps(observation_record(observation)))["type"] == (
        "raw.unknown"
    )
