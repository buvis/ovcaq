"""Public supervisor configuration and phase routing contracts."""

from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import cast, get_args

import pytest

from ovcaq.config import (
    AgentSettings,
    ConfigurationError,
    Effort,
    PhaseSettings,
    ResolvedPhaseRoute,
    RuntimeSettings,
    SupervisorSettings,
    agent_settings,
    resolve_phase_route,
    runtime_settings,
    supervisor_settings,
)
from ovcaq.runtime.decision import SupervisorPolicy

AGENT = (
    'agent = "local"\n[agents.local]\ncommand = ["runner"]\n'
    'tiers = { sonnet = "model-s", opus = "model-o", custom = "model-c" }\n'
)


@pytest.fixture
def config_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "user-config"))
    root = tmp_path / "project"
    root.mkdir()
    return root


def test_default_supervisor_settings_need_no_agent(config_root: Path) -> None:
    settings = supervisor_settings(config_root)

    assert isinstance(settings, SupervisorSettings)
    assert isinstance(settings.runtime, RuntimeSettings)
    assert settings.phases == {
        "build": PhaseSettings("sonnet", "high", 7200),
        "review": PhaseSettings("opus", "high", 10800),
        "done": PhaseSettings("sonnet", "high", 7200),
    }
    assert settings.policy == SupervisorPolicy(
        died_retries=1,
        connectivity_retries=3,
        rate_limit_retries=3,
        connectivity_wait_seconds=1800,
        rate_limit_wait_seconds=21600,
        phase_repeat_limit=5,
    )
    assert list(config_root.iterdir()) == []


def test_effort_lists_exactly_the_supported_values() -> None:
    assert set(get_args(Effort)) == {"low", "medium", "high", "xhigh"}


@pytest.mark.parametrize(
    "phase,tier,model,timeout",
    (
        ("build", "sonnet", "model-s", 7200),
        ("review", "opus", "model-o", 10800),
        ("done", "sonnet", "model-s", 7200),
    ),
)
def test_routes_resolve_neutral_defaults_to_selected_agent_models(
    config_root: Path, phase: str, tier: str, model: str, timeout: int
) -> None:
    (config_root / "ovcaq.toml").write_text(AGENT)

    route = resolve_phase_route(config_root, phase)

    assert route == ResolvedPhaseRoute(
        "local", phase, tier, model, "high", timeout, None
    )


def test_project_fields_override_user_fields_and_preserve_other_defaults(
    config_root: Path,
) -> None:
    user = config_root.parent / "user-config/ovcaq/config.toml"
    user.parent.mkdir(parents=True)
    user.write_text(
        '[phases.build]\ntier = "custom"\neffort = "low"\n'
        "timeout_seconds = 70\n[supervisor]\ndied_retries = 7\n"
        "connectivity_retries = 8\n"
    )
    (config_root / "ovcaq.toml").write_text(
        AGENT + '[phases.build]\neffort = "xhigh"\n[supervisor]\ndied_retries = 2\n'
    )

    settings = supervisor_settings(config_root)

    assert settings.phases["build"] == PhaseSettings("custom", "xhigh", 70)
    assert settings.phases["review"] == PhaseSettings("opus", "high", 10800)
    assert settings.policy.died_retries == 2
    assert settings.policy.connectivity_retries == 8
    assert settings.policy.rate_limit_retries == 3
    assert resolve_phase_route(config_root, "build").model == "model-c"


def test_agent_phase_overrides_merge_over_neutral_settings(config_root: Path) -> None:
    user = config_root.parent / "user-config/ovcaq/config.toml"
    user.parent.mkdir(parents=True)
    user.write_text('[agents.local.phases.build]\ntier = "custom"\n')
    (config_root / "ovcaq.toml").write_text(
        AGENT + '[phases.review]\neffort = "medium"\ntimeout_seconds = 83\n'
        '[agents.local.phases.review]\ntier = "custom"\neffort = "low"\n'
    )

    assert resolve_phase_route(config_root, "review") == ResolvedPhaseRoute(
        "local", "review", "custom", "model-c", "low", 83, None
    )
    assert resolve_phase_route(config_root, "build").model == "model-c"
    assert supervisor_settings(config_root).phases["review"].tier == "opus"


def test_done_route_uses_the_configured_tier_model(config_root: Path) -> None:
    (config_root / "ovcaq.toml").write_text(AGENT + '[phases.done]\ntier = "custom"\n')
    assert resolve_phase_route(config_root, "done").model == "model-c"


def test_explicit_agent_selection_controls_models_and_phase_overrides(
    config_root: Path,
) -> None:
    (config_root / "ovcaq.toml").write_text(
        AGENT + '[agents.other]\ncommand = ["other"]\n'
        'tiers = { sonnet = "other-s", opus = "other-o" }\n'
        '[agents.other.phases.build]\neffort = "low"\n'
    )

    assert resolve_phase_route(config_root, "build", agent="other") == (
        ResolvedPhaseRoute("other", "build", "sonnet", "other-s", "low", 7200, None)
    )


def test_explicit_settings_replace_each_complete_component(config_root: Path) -> None:
    (config_root / "ovcaq.toml").write_text(
        "[supervisor]\ndied_retries = 9\n[phases.build]\ntimeout_seconds = 9\n"
    )
    alternate = config_root.parent / "alternate"
    alternate.mkdir()
    runtime = runtime_settings(alternate)
    policy = SupervisorPolicy(2, 4, 6, 8, 10, 12)
    phases = {
        "build": PhaseSettings("a", "low", 1),
        "review": PhaseSettings("b", "medium", 2),
        "done": PhaseSettings("c", "xhigh", 3),
    }

    settings = supervisor_settings(
        config_root, runtime=runtime, policy=policy, phases=phases
    )

    assert settings.runtime == runtime
    assert settings.policy == policy
    assert settings.phases == phases


@pytest.mark.parametrize("component", ("runtime", "policy", "phases"))
def test_omitted_explicit_components_still_use_config(
    config_root: Path, component: str
) -> None:
    (config_root / "ovcaq.toml").write_text(
        "[supervisor]\ndied_retries = 9\n[phases.build]\ntimeout_seconds = 9\n"
    )
    baseline = supervisor_settings(config_root)
    explicit = {component: getattr(baseline, component)}

    assert supervisor_settings(config_root, **explicit) == baseline


@pytest.mark.parametrize(
    "explicit",
    (
        {"unknown": 1},
        {"runtime": {}},
        {"runtime": None},
        {"policy": {}},
        {"policy": None},
        {"phases": []},
        {"phases": None},
        {"phases": {}},
        {"phases": {"build": PhaseSettings("s", "high", 1)}},
    ),
)
def test_explicit_keywords_require_known_names_and_complete_typed_values(
    config_root: Path, explicit: dict[str, object]
) -> None:
    with pytest.raises(ConfigurationError):
        supervisor_settings(config_root, **explicit)


@pytest.mark.parametrize("extra", ("paused", "", "unknown"))
def test_explicit_phase_mapping_rejects_extra_nonroutable_keys(
    config_root: Path, extra: str
) -> None:
    phases = dict(supervisor_settings(config_root).phases)
    phases[extra] = PhaseSettings("sonnet", "high", 1)
    with pytest.raises(ConfigurationError):
        supervisor_settings(config_root, phases=phases)


def test_explicit_phase_mapping_rejects_untyped_values(config_root: Path) -> None:
    phases = dict(supervisor_settings(config_root).phases)
    phases["build"] = {"tier": "sonnet", "effort": "high", "timeout_seconds": 1}
    with pytest.raises(ConfigurationError):
        supervisor_settings(config_root, phases=phases)


@pytest.mark.parametrize("phase", ("paused", "", "unknown"))
def test_routes_reject_nonroutable_phases(config_root: Path, phase: str) -> None:
    (config_root / "ovcaq.toml").write_text(AGENT)
    with pytest.raises(ConfigurationError):
        resolve_phase_route(config_root, phase)


@pytest.mark.parametrize(
    "table",
    ('phases."paused"', 'phases.""', "phases.unknown", "agents.local.phases.paused"),
)
def test_config_rejects_nonroutable_phase_tables(config_root: Path, table: str) -> None:
    (config_root / "ovcaq.toml").write_text(AGENT + f'[{table}]\ntier = "sonnet"\n')
    with pytest.raises(ConfigurationError):
        resolve_phase_route(config_root, "build")


@pytest.mark.parametrize(
    "table,entry",
    (
        ("phases.build", 'model = "model-s"'),
        ("agents.local.phases.build", "timeout_seconds = 10"),
        ("agents.local.phases.build", 'unknown = "value"'),
        ("supervisor", "unknown = 1"),
    ),
)
def test_config_tables_reject_unrecognized_fields(
    config_root: Path, table: str, entry: str
) -> None:
    (config_root / "ovcaq.toml").write_text(AGENT + f"[{table}]\n{entry}\n")
    with pytest.raises(ConfigurationError):
        resolve_phase_route(config_root, "build")


@pytest.mark.parametrize("value", ("true", "false", "1.0", "0", "-1", "86401"))
def test_phase_timeout_rejects_noninteger_and_out_of_range_values(
    config_root: Path, value: str
) -> None:
    (config_root / "ovcaq.toml").write_text(
        f"[phases.build]\ntimeout_seconds = {value}\n"
    )
    with pytest.raises(ConfigurationError):
        supervisor_settings(config_root)


@pytest.mark.parametrize("value", (1, 42, 86400))
def test_phase_timeout_preserves_interior_and_inclusive_boundary_values(
    config_root: Path, value: int
) -> None:
    (config_root / "ovcaq.toml").write_text(
        AGENT + f"[phases.review]\ntimeout_seconds = {value}\n"
    )
    assert supervisor_settings(config_root).phases["review"].timeout_seconds == value
    assert resolve_phase_route(config_root, "review").timeout_seconds == value


@pytest.mark.parametrize("effort", ("low", "medium", "high", "xhigh"))
def test_phase_effort_accepts_each_supported_value(
    config_root: Path, effort: str
) -> None:
    (config_root / "ovcaq.toml").write_text(
        AGENT + f'[phases.build]\neffort = "{effort}"\n'
    )
    assert resolve_phase_route(config_root, "build").effort == effort


@pytest.mark.parametrize(
    "entry",
    ('effort = "max"', 'effort = ""', "effort = 1", 'tier = "missing"', 'tier = ""'),
)
def test_routes_reject_invalid_efforts_and_unknown_tiers(
    config_root: Path, entry: str
) -> None:
    (config_root / "ovcaq.toml").write_text(AGENT + f"[phases.build]\n{entry}\n")
    with pytest.raises(ConfigurationError):
        resolve_phase_route(config_root, "build")


@pytest.mark.parametrize(
    "key", ("died_retries", "connectivity_retries", "rate_limit_retries")
)
@pytest.mark.parametrize("value", ("-1", "true", "false", "1.0", '"1"'))
def test_policy_retry_counts_require_nonnegative_integers(
    config_root: Path, key: str, value: str
) -> None:
    (config_root / "ovcaq.toml").write_text(f"[supervisor]\n{key} = {value}\n")
    with pytest.raises(ConfigurationError):
        supervisor_settings(config_root)


@pytest.mark.parametrize(
    "key", ("connectivity_wait_seconds", "rate_limit_wait_seconds")
)
@pytest.mark.parametrize(
    "value", ("0", "-1", "true", "false", "nan", "inf", "-inf", '"1"')
)
def test_policy_waits_require_finite_positive_numbers(
    config_root: Path, key: str, value: str
) -> None:
    (config_root / "ovcaq.toml").write_text(f"[supervisor]\n{key} = {value}\n")
    with pytest.raises(ConfigurationError):
        supervisor_settings(config_root)


@pytest.mark.parametrize("value", ("0", "-1", "true", "false", "1.0"))
def test_phase_repeat_limit_requires_positive_integer(
    config_root: Path, value: str
) -> None:
    (config_root / "ovcaq.toml").write_text(
        f"[supervisor]\nphase_repeat_limit = {value}\n"
    )
    with pytest.raises(ConfigurationError):
        supervisor_settings(config_root)


def test_policy_accepts_zero_retries_fractional_waits_and_one_repeat(
    config_root: Path,
) -> None:
    (config_root / "ovcaq.toml").write_text(
        "[supervisor]\ndied_retries = 0\nconnectivity_retries = 0\n"
        "rate_limit_retries = 0\nconnectivity_wait_seconds = 0.5\n"
        "rate_limit_wait_seconds = 1\nphase_repeat_limit = 1\n"
    )
    assert supervisor_settings(config_root).policy == SupervisorPolicy(
        0, 0, 0, 0.5, 1, 1
    )


@pytest.mark.parametrize("key", ("rate_limit_retries", "phase_repeat_limit"))
def test_policy_preserves_configured_positive_limits(
    config_root: Path, key: str
) -> None:
    (config_root / "ovcaq.toml").write_text(f"[supervisor]\n{key} = 7\n")
    assert getattr(supervisor_settings(config_root).policy, key) == 7


@pytest.mark.parametrize("phase", ("build", "review", "done"))
def test_configured_prompts_remain_literal(config_root: Path, phase: str) -> None:
    literal = "  Run {phase} ${HOME} $(touch marker); ~ | literal  "
    (config_root / "ovcaq.toml").write_text(
        AGENT + f"[agents.local.prompts]\n{phase} = '{literal}'\n"
    )
    assert agent_settings(config_root).prompts == {phase: literal}
    assert resolve_phase_route(config_root, phase).prompt == literal
    assert not (config_root / "marker").exists()


@pytest.mark.parametrize(
    "entry",
    (
        'paused = "run"',
        'unknown = "run"',
        'build = ""',
        'build = "   "',
        "build = 1",
        "build = true",
        'build = "authorization=synthetic-value"',
        'build = "cookie: synthetic-value"',
        'build = "credential=synthetic-value"',
        'SERVICE_TOKEN_HEADER = "synthetic"',
    ),
)
def test_prompt_config_rejects_unknown_blank_wrong_type_and_credential_values(
    config_root: Path, entry: str
) -> None:
    (config_root / "ovcaq.toml").write_text(
        AGENT + f"[agents.local.prompts]\n{entry}\n"
    )
    with pytest.raises(ConfigurationError):
        agent_settings(config_root)


def test_direct_agent_prompts_default_to_empty_and_copy_immutable_input() -> None:
    empty = AgentSettings("local", ("runner",), {}, {}, {})
    prompts = {"build": "literal"}
    configured = AgentSettings("local", ("runner",), {}, {}, {}, prompts)
    prompts["build"] = "changed"

    assert empty.prompts == {}
    assert configured.prompts == {"build": "literal"}
    with pytest.raises(TypeError):
        cast(MutableMapping[str, str], configured.prompts)["build"] = "changed"


@pytest.mark.parametrize(
    "prompts",
    (
        {"build": "authorization=synthetic-value"},
        {"build": "AUTHORIZATION=synthetic-value"},
        {"review": "cookie: synthetic-value"},
        {"done": "credential=synthetic-value"},
        {"SERVICE_TOKEN_HEADER": "synthetic"},
    ),
)
def test_direct_agent_prompts_reject_credential_keys_and_values(
    prompts: dict[str, str],
) -> None:
    with pytest.raises(ConfigurationError):
        AgentSettings("local", ("runner",), {}, {}, {}, prompts)


def test_prompt_precedence_preserves_unoverridden_user_phase(config_root: Path) -> None:
    user = config_root.parent / "user-config/ovcaq/config.toml"
    user.parent.mkdir(parents=True)
    user.write_text(
        AGENT + '[agents.local.prompts]\nbuild = "user build"\nreview = "user review"\n'
    )
    (config_root / "ovcaq.toml").write_text(
        '[agents.local.prompts]\nbuild = "project build"\n'
    )
    assert resolve_phase_route(config_root, "build").prompt == "project build"
    assert resolve_phase_route(config_root, "review").prompt == "user review"
    assert resolve_phase_route(config_root, "done").prompt is None


def test_phase_records_are_frozen_and_slotted(config_root: Path) -> None:
    (config_root / "ovcaq.toml").write_text(AGENT)
    phase = PhaseSettings("sonnet", "high", 7200)
    route = resolve_phase_route(config_root, "build")
    settings = supervisor_settings(config_root)
    assert not hasattr(phase, "__dict__")
    assert not hasattr(route, "__dict__")
    assert not hasattr(settings, "__dict__")
    with pytest.raises(FrozenInstanceError):
        phase.tier = "opus"
    with pytest.raises(FrozenInstanceError):
        route.model = "other"
    with pytest.raises(FrozenInstanceError):
        settings.policy = settings.policy
    with pytest.raises(TypeError):
        cast(MutableMapping[str, PhaseSettings], settings.phases)["build"] = phase
