CLOSURE | resolved | 🟡 tests/runtime/test_adapter_health.py:33: Task 20 stopped passing a name to `fake_executable`, so its `name: str = "fixture-agent-health"` parameter is now dead | The diff drops the `name` parameter and sets `executable = directory / "fixture-agent-health"`.

CLOSURE | resolved | ⚪ tests/runtime/test_adapter_health.py:181: `test_claude_probe_rejects_sh_hidden_by_overlay_path` repeats the `[claude]` case of `test_probe_rejects_host_executable_hidden_by_overlay_path` | The diff deletes the whole `test_claude_probe_rejects_sh_hidden_by_overlay_path`. The diff does not touch the parametrized both-provider test, so it stays, as the task text says. The recorded run shows 23 passed.

NO FINDINGS
