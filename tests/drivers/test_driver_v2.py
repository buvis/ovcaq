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
    "driver_class", (ClaudeDriver, CodexDriver), ids=("claude", "codex")
)
def test_api_two_declares_default_tiers(
    driver_class: type[ClaudeDriver | CodexDriver],
) -> None:
    table = driver_class.default_tiers

    assert type(DRIVER_API_VERSION) is int
    assert DRIVER_API_VERSION == 2
    assert isinstance(table, Mapping)
    assert {"standard", "deep"} <= set(table)
    assert all(type(key) is str and type(value) is str for key, value in table.items())
    assert table.get("standar") is None
    assert table.get("deeper") is None
    with pytest.raises(TypeError):
        cast("MutableMapping[str, str]", table)["standard"] = "mutated-model"
    assert driver_class.default_tiers == table


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
