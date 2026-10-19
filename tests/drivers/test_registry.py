"""Required Claude driver discovery through the public versioned ABI."""

import sys

from ovcaq.config import AgentSettings
from ovcaq.drivers import DRIVER_API_VERSION, DriverPlugin, discover_drivers
from ovcaq.drivers.claude import ClaudeDriver


def test_claude_driver_discovers_through_public_plugin_abi() -> None:
    driver = ClaudeDriver(
        AgentSettings(
            name="claude",
            command=(sys.executable,),
            tiers={"standard": "fixture-model"},
            environment={},
            options={"permission_mode": "auto"},
        ),
        run_id="registry-run",
    )

    discovered = discover_drivers(
        (DriverPlugin(api_version=DRIVER_API_VERSION, factory=lambda: driver),),
        entry_points=(),
    )

    assert DRIVER_API_VERSION == 2
    assert tuple(discovered) == ("claude",)
    assert discovered["claude"] is driver
