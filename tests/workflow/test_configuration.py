from __future__ import annotations

from collections.abc import Mapping
from dataclasses import FrozenInstanceError
from pathlib import Path
from uuid import uuid4

import pytest

from ovcaq import drivers
from ovcaq.config import (
    DEFAULT_PHASE_TIERS,
    NEUTRAL_TIERS,
    AgentSettings,
    ConfigurationError,
    PhaseSettings,
    agent_settings,
    resolve_phase_route,
    workflow_settings,
)
from ovcaq.paths import ProjectPathError


@pytest.fixture
def config_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "user-config"))
    root = tmp_path / "project"
    root.mkdir()
    return root


@pytest.mark.parametrize(
    "declaration",
    (
        'workflow = "invalid"',
        "[workflow]\nprd_root = 12",
        '[workflow]\nruntime_root = ""',
        "agent = 12",
        'agent = "local"\n[agents.local]\ntiers = []',
    ),
)
def test_invalid_workflow_config_is_a_domain_error_without_effects(
    config_root: Path, declaration: str
) -> None:
    config = config_root / "ovcaq.toml"
    config.write_text(declaration)
    with pytest.raises(ConfigurationError):
        workflow_settings(config_root)
    assert list(config_root.iterdir()) == [config]


@pytest.mark.parametrize("escape", ("../outside", "amber", "quartz-17"))
def test_configured_runtime_preserves_containment_and_symlink_refusal(
    config_root: Path, escape: str
) -> None:
    external = config_root.parent / "outside"
    external.mkdir()
    if escape != "../outside":
        (config_root / escape).symlink_to(external, target_is_directory=True)
    with pytest.raises(ProjectPathError):
        workflow_settings(config_root, runtime_root=Path(escape))
    assert list(external.iterdir()) == []


@pytest.mark.parametrize("source", ("explicit", "configured"))
def test_workflow_paths_accept_contained_explicit_and_configured_values(
    config_root: Path, source: str
) -> None:
    prd_root = config_root / "requirements"
    runtime_root = config_root / "private"
    state_file = runtime_root / "workflow.json"
    arguments: dict[str, Path] = {}
    if source == "explicit":
        arguments = {
            "prd_root": prd_root,
            "runtime_root": runtime_root,
            "state_file": state_file,
        }
    else:
        (config_root / "ovcaq.toml").write_text(
            "[workflow]\n"
            f'prd_root = "{prd_root}"\n'
            f'runtime_root = "{runtime_root}"\n'
            f'state_file = "{state_file}"\n'
        )

    settings = workflow_settings(config_root, **arguments)

    assert settings.prd_root == prd_root
    assert settings.runtime_root == runtime_root
    assert settings.state_file == state_file


@pytest.mark.parametrize("source", ("explicit", "configured"))
@pytest.mark.parametrize(
    "unsafe_kind, component_name",
    (("escape", None), ("symlink", "amber"), ("symlink", "quartz-17")),
)
def test_workflow_prd_roots_reject_escapes_and_symlink_descendants(
    config_root: Path, source: str, unsafe_kind: str, component_name: str | None
) -> None:
    outside = config_root.parent / "outside-prds"
    outside.mkdir()
    unsafe = outside
    if unsafe_kind == "symlink":
        assert component_name is not None
        unsafe = config_root / component_name
        unsafe.symlink_to(outside, target_is_directory=True)

    arguments: dict[str, Path] = {}
    if source == "explicit":
        arguments["prd_root"] = unsafe
    else:
        (config_root / "ovcaq.toml").write_text(f'[workflow]\nprd_root = "{unsafe}"\n')

    with pytest.raises(ProjectPathError):
        workflow_settings(config_root, **arguments)
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("source", ("explicit", "configured"))
@pytest.mark.parametrize(
    "unsafe_kind, file_name",
    (("escape", None), ("symlink", "amber.dat"), ("symlink", "quartz-17.record")),
)
def test_workflow_state_files_reject_escapes_and_symlink_descendants(
    config_root: Path, source: str, unsafe_kind: str, file_name: str | None
) -> None:
    runtime_root = config_root / "private"
    runtime_root.mkdir()
    outside = config_root.parent / "outside-state.json"
    outside.write_text("preserve me")
    unsafe = outside
    if unsafe_kind == "symlink":
        assert file_name is not None
        unsafe = runtime_root / file_name
        unsafe.symlink_to(outside)

    arguments: dict[str, Path] = {}
    if source == "explicit":
        arguments = {"runtime_root": runtime_root, "state_file": unsafe}
    else:
        (config_root / "ovcaq.toml").write_text(
            f'[workflow]\nruntime_root = "{runtime_root}"\nstate_file = "{unsafe}"\n'
        )

    with pytest.raises(ProjectPathError):
        workflow_settings(config_root, **arguments)
    assert outside.read_text() == "preserve me"


def test_project_agent_selection_uses_only_its_merged_abstract_tier_keys(
    config_root: Path,
) -> None:
    user = config_root.parent / "user-config/ovcaq/config.toml"
    user.parent.mkdir(parents=True)
    user.write_text(
        'agent = "other"\n[agents.other]\ncommand = ["other-runner"]\n'
        'environment = {}\n[agents.other.tiers]\nunused = "opaque"\n'
        '[agents.active]\ncommand = ["runner"]\nenvironment = {}\n'
        '[agents.active.tiers]\nfast = "opaque"\n'
    )
    (config_root / "ovcaq.toml").write_text(
        'agent = "active"\n[agents.active.tiers]\ndeep = "opaque"\n'
    )
    assert workflow_settings(config_root).available_tiers == {
        "fast",
        "deep",
        "standard",
    }
    assert workflow_settings(config_root, available_tiers=[]).available_tiers == set()
    assert workflow_settings(
        config_root, available_tiers=["custom"]
    ).available_tiers == {"custom"}
    assert (
        workflow_settings(config_root).available_tiers
        == set(agent_settings(config_root).tiers) | NEUTRAL_TIERS
    )


@pytest.mark.parametrize("selection", ("explicit", "project", "user"))
def test_agent_name_uses_explicit_then_project_then_user_selection(
    config_root: Path, selection: str
) -> None:
    user = config_root.parent / "user-config/ovcaq/config.toml"
    user.parent.mkdir(parents=True)
    user.write_text(
        'version = 1\nagent = "user"\n'
        + "\n".join(
            f'[agents.{name}]\ncommand = ["{name}-runner"]\n'
            "tiers = {}\nenvironment = {}\noptions = {}\n"
            for name in ("explicit", "project", "user")
        )
    )
    if selection != "user":
        (config_root / "ovcaq.toml").write_text('agent = "project"\n')

    settings = agent_settings(
        config_root, name="explicit" if selection == "explicit" else None
    )

    assert settings.name == selection
    assert settings.command == (f"{selection}-runner",)
    assert settings.tiers == {}
    assert settings.environment == {}
    assert settings.options == {}


def test_agent_settings_accept_any_declared_valid_agent_name(
    config_root: Path,
) -> None:
    name = f"agent_{uuid4().hex}"
    (config_root / "ovcaq.toml").write_text(
        f'version = 1\nagent = "{name}"\n[agents.{name}]\n'
        f'command = ["{name}-runner", "--flag"]\n'
        "tiers = {}\nenvironment = {}\noptions = {}\n"
    )

    settings = agent_settings(config_root)

    assert settings.name == name
    assert settings.command == (f"{name}-runner", "--flag")


def test_agent_settings_preserve_fallback_model_tier_and_nonsecret_environment(
    config_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOST_ONLY_MARKER", "must-not-leak")
    monkeypatch.setenv("WARDEN_UNATTENDED", "host-value")
    (config_root / "ovcaq.toml").write_text(
        'agent = "claude"\n[agents.claude]\ncommand = ["claude"]\n'
        'tiers = { standard = "provider-primary", backup = "provider-backup" }\n'
        'environment = { WARDEN_UNATTENDED = "0", LOCAL_RUN_MODE = "batch" }\n'
        'options = { permission_mode = "auto", fallback_model = "backup" }\n'
    )

    settings = agent_settings(config_root)

    assert settings.tiers == {
        "standard": "provider-primary",
        "backup": "provider-backup",
    }
    assert settings.environment == {"WARDEN_UNATTENDED": "0", "LOCAL_RUN_MODE": "batch"}
    assert settings.options == {"permission_mode": "auto", "fallback_model": "backup"}


def test_agent_settings_merge_user_then_project_for_only_the_selected_agent(
    config_root: Path,
) -> None:
    user = config_root.parent / "user-config/ovcaq/config.toml"
    user.parent.mkdir(parents=True)
    user.write_text(
        'agent = "other"\n[agents.active]\ncommand = ["user-runner", "old"]\n'
        'tiers = { fast = "small", deep = "old-large" }\n'
        'environment = { MODE = "user", USER_ONLY = "yes" }\n'
        "options = { count = 2, quiet = false }\n"
        '[agents.other]\ncommand = ["other-runner"]\n'
        'tiers = { unused = "other" }\nenvironment = { OTHER_ONLY = "yes" }\n'
    )
    config = config_root / "ovcaq.toml"
    config.write_text(
        'version = 1\nagent = "active"\n[agents.active]\n'
        'command = ["project runner", "--literal", "$(touch forbidden)"]\n'
        'tiers = { deep = "large", balanced = "medium" }\n'
        'environment = { MODE = "project", PROJECT_ONLY = "yes" }\n'
        'options = { count = 0, labels = ["first", "second"] }\n'
    )

    settings = agent_settings(config_root)

    assert settings.name == "active"
    assert settings.command == (
        "project runner",
        "--literal",
        "$(touch forbidden)",
    )
    assert settings.tiers == {"fast": "small", "deep": "large", "balanced": "medium"}
    assert settings.environment == {
        "MODE": "project",
        "USER_ONLY": "yes",
        "PROJECT_ONLY": "yes",
    }
    assert set(settings.options) == {"count", "quiet", "labels"}
    assert settings.options["count"] == 0
    assert settings.options["quiet"] is False
    assert list(settings.options["labels"]) == ["first", "second"]
    assert list(config_root.iterdir()) == [config]


@pytest.mark.parametrize(
    "declaration",
    (
        "",
        'agent = ""',
        "agent = 12",
        "agent = false",
    ),
)
def test_agent_settings_reject_missing_empty_or_non_string_selection(
    config_root: Path, declaration: str
) -> None:
    (config_root / "ovcaq.toml").write_text(declaration)
    with pytest.raises(ConfigurationError):
        agent_settings(config_root)


def test_selected_agent_without_a_declaration_defaults_command_to_its_name(
    config_root: Path,
) -> None:
    (config_root / "ovcaq.toml").write_text('agent = "missing"\n')

    settings = agent_settings(config_root)

    assert settings.name == "missing"
    assert settings.command == ("missing",)
    assert settings.tiers == {}
    assert settings.environment == {}
    assert settings.options == {}


def test_empty_explicit_agent_name_does_not_fall_back_to_configured_selection(
    config_root: Path,
) -> None:
    (config_root / "ovcaq.toml").write_text(
        'agent = "local"\n[agents.local]\ncommand = ["runner"]\n'
        "tiers = {}\nenvironment = {}\noptions = {}\n"
    )
    with pytest.raises(ConfigurationError):
        agent_settings(config_root, name="")


@pytest.mark.parametrize(
    "field, value",
    (
        ("command", '"runner --flag"'),
        ("command", "[]"),
        ("command", '[""]'),
        ("command", '["runner", 3]'),
        ("command", '["runner", ""]'),
        ("tiers", "[]"),
        ("tiers", '{ "" = "model" }'),
        ("tiers", '{ fast = "" }'),
        ("tiers", "{ fast = 3 }"),
        ("environment", '"MODE=local"'),
        ("environment", '{ "" = "value" }'),
        ("environment", '{ MODE = "" }'),
        ("environment", "{ MODE = false }"),
        ("options", "[]"),
        ("options", "{ date = 2026-09-26 }"),
        ("options", "{ value = nan }"),
        ("options", "{ value = inf }"),
    ),
)
def test_agent_settings_reject_invalid_argv_tables_and_non_json_options(
    config_root: Path, field: str, value: str
) -> None:
    fields = {
        "command": '["runner"]',
        "tiers": "{}",
        "environment": "{}",
        "options": "{}",
    }
    fields[field] = value
    config = config_root / "ovcaq.toml"
    config.write_text(
        'agent = "local"\n[agents.local]\n'
        + "\n".join(f"{key} = {item}" for key, item in fields.items())
    )
    before = config.read_bytes()

    with pytest.raises(ConfigurationError):
        agent_settings(config_root)

    assert config.read_bytes() == before
    assert list(config_root.iterdir()) == [config]


def test_agent_settings_default_omitted_command_to_selected_name(
    config_root: Path,
) -> None:
    (config_root / "ovcaq.toml").write_text(
        'agent = "local"\n[agents.local]\ntiers = {}\nenvironment = {}\noptions = {}\n'
    )
    settings = agent_settings(config_root)
    assert settings.name == "local"
    assert settings.command == ("local",)


@pytest.mark.parametrize("table", ("environment", "options"))
@pytest.mark.parametrize(
    "entry",
    (
        'API_KEY = "example"',
        'apiKey = "example"',
        'ACCESS_TOKEN = "example"',
        'CLIENT_SECRET = "example"',
        'PASSWORD = "example"',
        'VALUE = "Bearer example-token"',
        'VALUE = "api_key=example"',
        'VALUE = "token=example"',
        'VALUE = "password=example"',
        'VALUE = "secret=example"',
    ),
)
def test_agent_settings_reject_credential_shaped_keys_and_values(
    config_root: Path, table: str, entry: str
) -> None:
    other = "options" if table == "environment" else "environment"
    config = config_root / "ovcaq.toml"
    config.write_text(
        'agent = "local"\n[agents.local]\ncommand = ["runner"]\ntiers = {}\n'
        f"{other} = {{}}\n{table} = {{ {entry} }}\n"
    )
    before = config.read_bytes()

    with pytest.raises(ConfigurationError):
        agent_settings(config_root)

    assert config.read_bytes() == before
    assert list(config_root.iterdir()) == [config]


@pytest.mark.parametrize(
    "value",
    ('[{ api_key = "example" }]', '[{ value = "password=example" }]'),
)
def test_agent_settings_reject_credentials_nested_in_option_arrays(
    config_root: Path, value: str
) -> None:
    (config_root / "ovcaq.toml").write_text(
        'agent = "local"\n[agents.local]\ncommand = ["runner"]\n'
        "tiers = {}\nenvironment = {}\n"
        f"options = {{ nested = {value} }}\n"
    )
    with pytest.raises(ConfigurationError):
        agent_settings(config_root)


@pytest.mark.parametrize(
    "key",
    ("TOKENIZER", "PASSWORDLESS", "SECRETARY"),
)
def test_agent_settings_reject_credential_substrings_in_keys(
    config_root: Path,
    key: str,
) -> None:
    (config_root / "ovcaq.toml").write_text(
        'agent = "local"\n[agents.local]\ncommand = ["runner"]\ntiers = {}\n'
        f'environment = {{ {key} = "synthetic" }}\noptions = {{}}\n'
    )

    with pytest.raises(ConfigurationError):
        agent_settings(config_root)


def test_agent_settings_copy_and_recursively_freeze_constructor_inputs() -> None:
    tiers = {"fast": "small"}
    environment = {"MODE": "local"}
    nested = {"enabled": True}
    values = ["first", nested, None]
    options = {"values": values, "count": 2, "ratio": 0.5}
    settings = AgentSettings(
        name="local",
        command=("runner", "--flag"),
        tiers=tiers,
        environment=environment,
        options=options,
    )
    tiers["fast"] = "changed"
    environment["MODE"] = "changed"
    nested["enabled"] = False
    values.append("changed")
    options["count"] = 99

    assert settings.tiers == {"fast": "small"}
    assert settings.environment == {"MODE": "local"}
    assert settings.options["count"] == 2
    assert settings.options["ratio"] == 0.5
    assert list(settings.options["values"]) == ["first", {"enabled": True}, None]
    with pytest.raises(FrozenInstanceError):
        settings.name = "changed"
    with pytest.raises(TypeError):
        settings.command[0] = "changed"
    with pytest.raises(TypeError):
        settings.tiers["fast"] = "changed"
    with pytest.raises(TypeError):
        settings.environment["MODE"] = "changed"
    with pytest.raises(TypeError):
        settings.options["count"] = 99
    with pytest.raises(TypeError):
        settings.options["values"][0] = "changed"
    with pytest.raises(TypeError):
        settings.options["values"][1]["enabled"] = False


def test_loaded_agent_settings_remain_immutable_and_independent_of_later_loads(
    config_root: Path,
) -> None:
    config = config_root / "ovcaq.toml"
    config.write_text(
        'agent = "local"\n[agents.local]\ncommand = ["runner"]\n'
        'tiers = { fast = "small" }\nenvironment = { MODE = "local" }\n'
        "options = { nested = [{ enabled = true }] }\n"
    )
    first = agent_settings(config_root)
    config.write_text(
        'agent = "local"\n[agents.local]\ncommand = ["changed-runner"]\n'
        'tiers = { fast = "large" }\nenvironment = { MODE = "changed" }\n'
        "options = { nested = [{ enabled = false }] }\n"
    )
    second = agent_settings(config_root)

    assert first.command == ("runner",)
    assert first.tiers == {"fast": "small"}
    assert first.environment == {"MODE": "local"}
    assert first.options["nested"][0]["enabled"] is True
    assert second.command == ("changed-runner",)
    assert second.tiers == {"fast": "large"}
    assert second.environment == {"MODE": "changed"}
    assert second.options["nested"][0]["enabled"] is False
    with pytest.raises(TypeError):
        first.tiers["fast"] = "changed"
    with pytest.raises(TypeError):
        first.environment["MODE"] = "changed"
    with pytest.raises(TypeError):
        first.options["nested"][0]["enabled"] = False


def test_neutral_default_tiers_are_always_available(config_root: Path) -> None:
    assert DEFAULT_PHASE_TIERS == {
        "build": "standard",
        "review": "deep",
        "done": "standard",
    }
    assert NEUTRAL_TIERS == frozenset(DEFAULT_PHASE_TIERS.values())
    assert NEUTRAL_TIERS == frozenset({"standard", "deep"})
    assert isinstance(NEUTRAL_TIERS, frozenset)

    config = config_root / "ovcaq.toml"
    config.write_text('agent = "active"\n')

    assert workflow_settings(config_root).available_tiers == {"standard", "deep"}
    assert workflow_settings(config_root).available_tiers == set(NEUTRAL_TIERS)

    config.write_text(
        'agent = "active"\n[agents.active]\ncommand = ["runner"]\n'
        "environment = {}\n[agents.active.tiers]\n"
        'standard_plus = "opaque-one"\ndeeper = "opaque-two"\n'
    )

    assert workflow_settings(config_root).available_tiers == {
        "standard_plus",
        "deeper",
        "standard",
        "deep",
    }
    assert (
        workflow_settings(config_root).available_tiers
        == set(agent_settings(config_root).tiers) | NEUTRAL_TIERS
    )


def test_drivers_no_longer_publish_the_default_phase_tier_table() -> None:
    assert not hasattr(drivers, "DEFAULT_PHASE_TIERS")
    assert "DEFAULT_PHASE_TIERS" not in drivers.__all__
    assert "DEFAULT_PHASE_TIERS" not in dir(drivers)
    assert [
        name
        for name, value in vars(drivers).items()
        if isinstance(value, Mapping) and set(value) == set(DEFAULT_PHASE_TIERS)
    ] == []


@pytest.mark.parametrize(
    "phase, tier, model",
    (("build", "fast", "opaque-small"), ("review", "slow", "opaque-large")),
)
def test_route_without_default_tiers_resolves_a_configured_tier(
    config_root: Path, phase: str, tier: str, model: str
) -> None:
    (config_root / "ovcaq.toml").write_text(
        'agent = "active"\n[agents.active]\ncommand = ["runner"]\n'
        "environment = {}\n[agents.active.tiers]\n"
        'fast = "opaque-small"\nslow = "opaque-large"\n'
    )

    route = resolve_phase_route(
        config_root,
        phase,
        phase_settings=PhaseSettings(tier, "high", 1234),
        default_tiers=None,
    )

    assert route.agent == "active"
    assert route.phase == phase
    assert route.tier == tier
    assert route.model == model
    assert route.effort == "high"
    assert route.timeout_seconds == 1234


@pytest.mark.parametrize("default_tiers", (None, {}))
@pytest.mark.parametrize("tier", ("standard", "deep"))
def test_route_names_the_unknown_agent_tier_it_cannot_resolve(
    config_root: Path, default_tiers: dict[str, str] | None, tier: str
) -> None:
    (config_root / "ovcaq.toml").write_text(
        'agent = "active"\n[agents.active]\ncommand = ["runner"]\n'
        'environment = {}\n[agents.active.tiers]\nfast = "opaque-small"\n'
    )

    with pytest.raises(ConfigurationError) as error:
        resolve_phase_route(
            config_root,
            "build",
            phase_settings=PhaseSettings(tier, "medium", 600),
            default_tiers=default_tiers,
        )

    assert str(error.value) == f"Unknown agent tier: {tier}"


def test_default_tiers_supply_models_the_agent_has_not_configured(
    config_root: Path,
) -> None:
    user = config_root.parent / "user-config/ovcaq/config.toml"
    user.parent.mkdir(parents=True)
    user.write_text('[agents.active.tiers]\nslow = "opaque-user"\n')
    (config_root / "ovcaq.toml").write_text(
        'agent = "active"\n[agents.active]\ncommand = ["runner"]\n'
        'environment = {}\n[agents.active.tiers]\nfast = "opaque-small"\n'
    )
    defaults = {
        "standard": "opaque-standard",
        "deep": "opaque-deep",
        "turbo": "opaque-turbo",
    }
    routes = {
        tier: resolve_phase_route(
            config_root,
            phase,
            phase_settings=PhaseSettings(tier, "medium", 600),
            default_tiers=defaults,
        )
        for phase, tier in (
            ("build", "standard"),
            ("review", "deep"),
            ("done", "fast"),
            ("build", "slow"),
            ("done", "turbo"),
        )
    }

    assert routes["standard"].model == "opaque-standard"
    assert routes["deep"].model == "opaque-deep"
    assert routes["fast"].model == "opaque-small"
    assert routes["slow"].model == "opaque-user"
    assert routes["turbo"].model == "opaque-turbo"
    assert [route.tier for route in routes.values()] == [
        "standard",
        "deep",
        "fast",
        "slow",
        "turbo",
    ]
    assert [route.effort for route in routes.values()] == ["medium"] * 5
    assert [route.timeout_seconds for route in routes.values()] == [600] * 5


def test_configured_tier_shadows_a_default_tier_of_the_same_key(
    config_root: Path,
) -> None:
    (config_root / "ovcaq.toml").write_text(
        'agent = "active"\n[agents.active]\ncommand = ["runner"]\n'
        'environment = {}\n[agents.active.tiers]\ndeep = "opaque-configured"\n'
    )
    defaults = {"deep": "opaque-default-deep", "standard": "opaque-default-standard"}

    shadowed = resolve_phase_route(
        config_root,
        "review",
        phase_settings=PhaseSettings("deep", "medium", 600),
        default_tiers=defaults,
    )
    inherited = resolve_phase_route(
        config_root,
        "build",
        phase_settings=PhaseSettings("standard", "medium", 600),
        default_tiers=defaults,
    )

    assert shadowed.model == "opaque-configured"
    assert inherited.model == "opaque-default-standard"


@pytest.mark.parametrize("phase", ("build", "review", "done"))
def test_omitted_phase_settings_route_through_the_neutral_phase_defaults(
    config_root: Path, phase: str
) -> None:
    (config_root / "ovcaq.toml").write_text(
        'agent = "active"\n[agents.active]\ncommand = ["runner"]\n'
        'environment = {}\n[agents.active.tiers]\nfast = "opaque-small"\n'
    )
    defaults = {"standard": "opaque-standard", "deep": "opaque-deep"}

    route = resolve_phase_route(config_root, phase, default_tiers=defaults)

    assert route.phase == phase
    assert route.tier == DEFAULT_PHASE_TIERS[phase]
    assert route.model == defaults[DEFAULT_PHASE_TIERS[phase]]


def test_per_agent_phase_tier_overrides_the_neutral_phase_default(
    config_root: Path,
) -> None:
    (config_root / "ovcaq.toml").write_text(
        'agent = "active"\n[agents.active]\ncommand = ["runner"]\n'
        'environment = {}\n[agents.active.tiers]\nfast = "opaque-small"\n'
        '[agents.active.phases.review]\ntier = "fast"\n'
    )

    route = resolve_phase_route(
        config_root, "review", default_tiers={"deep": "opaque-deep"}
    )

    assert route.tier == "fast"
    assert route.model == "opaque-small"


def test_route_resolves_tiers_of_the_explicitly_named_agent(
    config_root: Path,
) -> None:
    (config_root / "ovcaq.toml").write_text(
        'agent = "active"\n[agents.active]\ncommand = ["runner"]\n'
        'environment = {}\n[agents.active.tiers]\nfast = "opaque-active"\n'
        '[agents.other]\ncommand = ["other-runner"]\nenvironment = {}\n'
        '[agents.other.tiers]\nfast = "opaque-other"\n'
    )

    route = resolve_phase_route(
        config_root,
        "build",
        agent="other",
        phase_settings=PhaseSettings("fast", "medium", 600),
        default_tiers={"standard": "opaque-standard"},
    )

    assert route.agent == "other"
    assert route.model == "opaque-other"


@pytest.mark.parametrize(
    "tier, defaults",
    (
        ("standard", {"standardized": "opaque-near-default"}),
        ("deep", {"deeper": "opaque-near-default"}),
    ),
)
def test_route_rejects_a_tier_only_resembling_a_known_key(
    config_root: Path, tier: str, defaults: dict[str, str]
) -> None:
    (config_root / "ovcaq.toml").write_text(
        'agent = "active"\n[agents.active]\ncommand = ["runner"]\n'
        'environment = {}\n[agents.active.tiers]\nfastest = "opaque-small"\n'
    )

    with pytest.raises(ConfigurationError) as error:
        resolve_phase_route(
            config_root,
            "done",
            phase_settings=PhaseSettings(tier, "low", 60),
            default_tiers=defaults,
        )

    assert str(error.value) == f"Unknown agent tier: {tier}"
