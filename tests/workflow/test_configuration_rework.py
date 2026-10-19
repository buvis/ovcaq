from __future__ import annotations

from pathlib import Path

import pytest

from ovcaq.config import (
    AgentSettings,
    ConfigurationError,
    agent_settings,
    workflow_settings,
)


@pytest.fixture
def config_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "user-config"))
    root = tmp_path / "project"
    root.mkdir()
    return root


def test_workflow_settings_load_without_an_agent_selection(config_root: Path) -> None:
    config = config_root / "ovcaq.toml"
    config.write_text('[workflow]\nprd_root = "requirements"\n')

    settings = workflow_settings(config_root)

    assert settings.prd_root == config_root / "requirements"
    assert settings.available_tiers == set()
    assert config.read_text() == '[workflow]\nprd_root = "requirements"\n'


def test_workflow_settings_validate_the_selected_agent(config_root: Path) -> None:
    (config_root / "ovcaq.toml").write_text(
        'agent = "local"\n[agents.local]\ncommand = []\n'
    )

    with pytest.raises(ConfigurationError):
        workflow_settings(config_root)


@pytest.mark.parametrize("table", ("environment", "options"))
@pytest.mark.parametrize(
    "entry",
    (
        'AUTHORIZATION = "synthetic"',
        'Cookie = "synthetic"',
        'clientCredential = "synthetic"',
        'clientcredential = "synthetic"',
        '"service-api-key-file" = "synthetic"',
        'VALUE = "authorization=synthetic-value"',
        'VALUE = "cookie: synthetic-value"',
        'VALUE = "credential=synthetic-value"',
        'VALUE = "sk-synthetic_' + 'Q7v-k9_42mN8p23R4j62y"',
        'VALUE = "sk-test-synthetic-' + 'Q7v_k9-42mN8p23R4j62y"',
    ),
)
def test_agent_settings_reject_additional_credential_keys_and_pinned_values(
    config_root: Path, table: str, entry: str
) -> None:
    other = "options" if table == "environment" else "environment"
    (config_root / "ovcaq.toml").write_text(
        'agent = "local"\n[agents.local]\ncommand = ["runner"]\ntiers = {}\n'
        f"{other} = {{}}\n{table} = {{ {entry} }}\n"
    )

    with pytest.raises(ConfigurationError):
        agent_settings(config_root)


@pytest.mark.parametrize(
    "key",
    (
        "SERVICE_TOKEN_HEADER",
        "CLIENT_SECRET_VALUE",
        "DATABASE_PASSWORD_FILE",
        "HEADER_AUTHORIZATION_MODE",
        "PRIMARY_API_KEY_PATH",
        "SESSION_COOKIE_VALUE",
        "CLIENT_CREDENTIAL_FILE",
        "clientcredential",
        "service-api-key-file",
    ),
)
@pytest.mark.parametrize("table", ("environment", "options"))
def test_direct_agent_settings_reject_credential_key_substrings(
    table: str, key: str
) -> None:
    environment = {key: "synthetic"} if table == "environment" else {}
    options = {key: "synthetic"} if table == "options" else {}
    with pytest.raises(ConfigurationError):
        AgentSettings(
            name="local",
            command=("local",),
            tiers={},
            environment=environment,
            options=options,
        )


@pytest.mark.parametrize(
    "environment,options",
    (
        ({"MODE": "authorization=synthetic-value"}, {}),
        ({"MODE": "sk-synthetic_" + "Q7v-k9_42mN8p23R4j62y"}, {}),
        ({}, {"value": "cookie: synthetic-value"}),
        ({}, {"value": "sk-test-synthetic-" + "Q7v_k9-42mN8p23R4j62y"}),
        ({}, {"nested": [{"value": "credential=synthetic-value"}]}),
    ),
)
def test_direct_agent_settings_reject_pinned_credential_values(
    environment: dict[str, str], options: dict[str, object]
) -> None:
    with pytest.raises(ConfigurationError):
        AgentSettings(
            name="local",
            command=("local",),
            tiers={},
            environment=environment,
            options=options,
        )


def test_agent_settings_allow_ordinary_environment_controls(config_root: Path) -> None:
    (config_root / "ovcaq.toml").write_text(
        'agent = "local"\n[agents.local]\ncommand = ["runner"]\n'
        "tiers = {}\noptions = {}\n"
        'environment = { TERM = "dumb", NO_COLOR = "1", CI = "true" }\n'
    )

    settings = agent_settings(config_root)

    assert settings.command == ("runner",)
    assert settings.environment == {"TERM": "dumb", "NO_COLOR": "1", "CI": "true"}


def test_direct_agent_settings_accept_a_valid_construction() -> None:
    settings = AgentSettings(
        name="agent",
        command=("agent",),
        tiers={"standard": "model-a"},
        environment={},
        options={},
    )

    assert settings.name == "agent"
    assert settings.command == ("agent",)
    assert settings.tiers == {"standard": "model-a"}


@pytest.mark.parametrize(
    "name,command,tiers",
    (
        ("", ("agent",), {"standard": "model-a"}),
        ("agent", (), {"standard": "model-a"}),
        ("agent", ("claude", ""), {"standard": "model-a"}),
        ("agent", ("agent",), {"": "model-a"}),
        ("agent", ("agent",), {"standard": ""}),
    ),
    ids=(
        "empty-name",
        "empty-command",
        "blank-command-part",
        "empty-tier-key",
        "empty-tier-value",
    ),
)
def test_direct_agent_settings_reject_empty_name_command_and_tier_parts(
    name: str, command: tuple[str, ...], tiers: dict[str, str]
) -> None:
    with pytest.raises(ConfigurationError):
        AgentSettings(
            name=name, command=command, tiers=tiers, environment={}, options={}
        )
