# Split note: 00063-driver-failure-classes-tiers-v1.md
planned=6 prd_tasks=5 expansion=1.20 reasons=module_drift

## tests/integration (UNLISTED)

- 5 Thread default_tiers through resolve_phase_route and the supervisor, and migrate every fixture off the old tier keys: tests/integration/test_observer_terminal_cleanup.py, tests/integration/test_supervisor_live_telemetry.py

## tests/packaging (UNLISTED)

- 5 Thread default_tiers through resolve_phase_route and the supervisor, and migrate every fixture off the old tier keys: tests/packaging/test_installed_supervisor_cli.py

## tests/runtime (UNLISTED)

- 5 Thread default_tiers through resolve_phase_route and the supervisor, and migrate every fixture off the old tier keys: tests/runtime/test_adapter_launch_routing.py, tests/runtime/test_supervisor_preflight.py, tests/runtime/test_supervisor.py, tests/runtime/test_supervisor_adapters.py, tests/runtime/test_rework_health.py, tests/runtime/test_adapter_health.py, tests/runtime/test_supervisor_process.py

## tests/workflow (UNLISTED)

- 3 Move DEFAULT_PHASE_TIERS to config.py with neutral values and add the keys to available_tiers: tests/workflow/test_configuration.py
- 5 Thread default_tiers through resolve_phase_route and the supervisor, and migrate every fixture off the old tier keys: tests/workflow/test_supervisor_configuration.py

## . (listed)

- 6 Document the neutral keys, the driver default tables and the new failure markers: CHANGELOG.md

## docs (listed)

- 6 Document the neutral keys, the driver default tables and the new failure markers: docs/driver-protocol.md, docs/operations.md

## src/ovcaq (listed)

- 3 Move DEFAULT_PHASE_TIERS to config.py with neutral values and add the keys to available_tiers: src/ovcaq/config.py
- 5 Thread default_tiers through resolve_phase_route and the supervisor, and migrate every fixture off the old tier keys: src/ovcaq/config.py

## src/ovcaq/drivers (listed)

- 1 Add the Claude failure markers and a table test: src/ovcaq/drivers/claude_events.py
- 2 Add the Codex failure alternatives and pin the hold 00056 wording: src/ovcaq/drivers/codex_events.py
- 3 Move DEFAULT_PHASE_TIERS to config.py with neutral values and add the keys to available_tiers: src/ovcaq/drivers/__init__.py
- 4 Add default_tiers to the driver protocol and both drivers: src/ovcaq/drivers/base.py, src/ovcaq/drivers/claude.py, src/ovcaq/drivers/codex.py

## src/ovcaq/runtime (listed)

- 5 Thread default_tiers through resolve_phase_route and the supervisor, and migrate every fixture off the old tier keys: src/ovcaq/runtime/supervisor.py

## tests/drivers (listed)

- 1 Add the Claude failure markers and a table test: tests/drivers/test_adapter_failure_classes.py
- 2 Add the Codex failure alternatives and pin the hold 00056 wording: tests/drivers/test_adapter_failure_classes.py
- 4 Add default_tiers to the driver protocol and both drivers: tests/drivers/test_driver_v2.py, tests/drivers/test_claude_launch.py, tests/drivers/test_codex_launch.py
