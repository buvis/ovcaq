CLOSURE | resolved | "Only Claude has a test for this... Parametrize the test over ("claude", "codex") and drop "claude" from its name." | The diff adds `@pytest.mark.parametrize("provider", ("claude", "codex"))`, renames the test to `test_probe_uses_default_search_path_when_host_path_is_absent`, and passes `provider` to both `driver_for` and `assert_probe_evidence`. The recorded run shows 2 passed, so both providers ran and passed.

NO FINDINGS
