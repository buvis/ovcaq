"""Driver API 2 owns provider-specific default prompts."""

import sys
from collections.abc import Mapping, MutableMapping
from typing import cast

import pytest

from ovcaq.config import AgentSettings
from ovcaq.drivers import DRIVER_API_VERSION, AgentDriver
from ovcaq.drivers.claude import ClaudeDriver
from ovcaq.drivers.codex import CodexDriver


@pytest.fixture
def driver() -> ClaudeDriver:
    return ClaudeDriver(
        AgentSettings(
            name="claude",
            command=(sys.executable,),
            tiers={"standard": "fixture-model"},
            environment={},
            options={"permission_mode": "auto"},
        ),
        run_id="prompt-contract",
    )


def test_api_two_declares_the_default_prompt_protocol() -> None:
    assert type(DRIVER_API_VERSION) is int
    assert DRIVER_API_VERSION == 2
    assert callable(AgentDriver.default_prompt)


@pytest.mark.parametrize(
    ("driver_class", "expected"),
    (
        (ClaudeDriver, {"standard": "sonnet", "deep": "opus"}),
        (CodexDriver, {"standard": "default", "deep": "default"}),
    ),
    ids=("claude", "codex"),
)
def test_api_two_declares_default_tiers(
    driver_class: type[ClaudeDriver | CodexDriver],
    expected: dict[str, str],
) -> None:
    table = driver_class.default_tiers
    mutable = cast("MutableMapping[str, str]", table)

    assert type(DRIVER_API_VERSION) is int
    assert DRIVER_API_VERSION == 2
    assert isinstance(table, Mapping)
    assert dict(table) == expected
    assert all(type(key) is str and type(value) is str for key, value in table.items())
    assert all(value.strip() == value and value for value in table.values())
    assert table.get("standar") is None
    assert table.get("deeper") is None
    with pytest.raises(TypeError):
        mutable["standard"] = "mutated-model"
    with pytest.raises((TypeError, AttributeError)):
        mutable.update({"standard": "mutated-model"})
    with pytest.raises((TypeError, AttributeError)):
        mutable.setdefault("standard", "mutated-model")
    with pytest.raises((TypeError, AttributeError)):
        mutable.setdefault("extra-tier", "mutated-model")
    with pytest.raises((TypeError, AttributeError)):
        mutable.pop("standard")
    with pytest.raises((TypeError, AttributeError)):
        del mutable["standard"]
    assert dict(driver_class.default_tiers) == expected


@pytest.mark.parametrize("phase", ("build", "review", "done"))
def test_claude_default_prompt_is_the_literal_autopilot_command(
    driver: ClaudeDriver, phase: str
) -> None:
    assert driver.default_prompt(phase) == "/autopilot:run-autopilot"


@pytest.mark.parametrize("phase", ("paused", "", "unknown", "BUILD", " build"))
def test_claude_default_prompt_rejects_nonroutable_phases(
    driver: ClaudeDriver, phase: str
) -> None:
    with pytest.raises(ValueError):
        driver.default_prompt(phase)
