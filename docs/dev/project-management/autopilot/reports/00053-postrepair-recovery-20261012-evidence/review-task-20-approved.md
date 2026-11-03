CLOSURE | resolved | "tests/runtime/test_adapter_health.py:90 runs `command_name` over three names ... 6 cases where 2 would do. Keep one name" | The diff drops the `command_name` parametrize and argument. Only `@pytest.mark.parametrize("provider", ("claude", "codex"))` remains. The recorded run shows 2 passed, down from 6.

NO FINDINGS
