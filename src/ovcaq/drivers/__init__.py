"""Public driver contract and discovery API."""

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

# Default tier keys per routable phase; tier names stay at the driver edge.
DEFAULT_PHASE_TIERS = {"build": "sonnet", "review": "opus", "done": "sonnet"}

__all__ = [
    "DEFAULT_PHASE_TIERS",
    "DRIVER_API_VERSION",
    "AgentDriver",
    "DriverDiscoveryError",
    "DriverFactory",
    "DriverHealth",
    "DriverPlugin",
    "DuplicateDriverError",
    "IncompatibleDriverError",
    "LaunchRequest",
    "LaunchSpec",
    "discover_drivers",
]
