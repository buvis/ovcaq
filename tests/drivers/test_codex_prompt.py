from pathlib import Path

import pytest

from ovcaq.config import (
    AgentSettings,
    PhaseSettings,
    agent_settings,
    resolve_phase_route,
)
from ovcaq.drivers.codex import CodexDriver
from ovcaq.paths import CONFIG_NAME

PROMPT_CONTRACT = """Read the committed OVCAQ state to determine the current phase. Use `ovcaq state`
and `ovcaq workflow` commands for all durable mutations. Perform only the
current phase, commit exactly one successful phase handoff through the OVCAQ
workflow command, then exit the session. Never edit state.json directly. Do not
start a second phase in this session. Completion is determined by committed
state, not your final message. Do not install, upgrade, or modify launcher
plugins or marketplace content."""
NATIVE_PROMPT = f"$run-autopilot\n{PROMPT_CONTRACT}"


@pytest.fixture
def driver() -> CodexDriver:
    settings = AgentSettings(
        name="codex",
        command=("fixture-wrapper", "--literal-prefix", "fixture-launcher"),
        tiers={"standard": "fixture-model", "premium": "fixture-large"},
        environment={"TASK_MODE": "fixture", "TASK_LABEL": "two words"},
        options={},
    )
    return CodexDriver(settings, run_id="prompt-run")


@pytest.mark.parametrize("phase", ["build", "review", "done"])
def test_default_prompt_invokes_native_skill_with_state_only_handoff(
    driver: CodexDriver, phase: str
) -> None:
    prompt = driver.default_prompt(phase)

    assert prompt == NATIVE_PROMPT
    assert prompt.startswith("$run-autopilot\n")
    assert prompt.count("$run-autopilot") == 1
    assert "Never edit state.json directly." in prompt
    assert "Do not\nstart a second phase in this session." in prompt


@pytest.mark.parametrize("phase", ["", "prepare", "READY", "build ", None])
def test_default_prompt_rejects_phases_outside_the_canonical_allowlist(
    driver: CodexDriver, phase: object
) -> None:
    with pytest.raises(ValueError):
        driver.default_prompt(phase)  # type: ignore[arg-type]


def test_configured_prompts_remain_literal_phase_overrides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    (project / CONFIG_NAME).write_text(
        'agent = "codex"\n'
        '[agents.codex.tiers]\nstandard = "fixture-model"\n'
        "[agents.codex.prompts]\n"
        "build = 'Build ${HOME} $(touch injected); literal'\n"
        "review = 'Review --literal-prompt; separate'\n"
        "done = 'Finish $run-autopilot; configured'\n",
        encoding="utf-8",
    )

    settings = agent_settings(project)

    assert settings.prompts == {
        "build": "Build ${HOME} $(touch injected); literal",
        "review": "Review --literal-prompt; separate",
        "done": "Finish $run-autopilot; configured",
    }
    driver = CodexDriver(settings, run_id="configured-prompt-run")
    for phase in ("build", "review", "done"):
        route = resolve_phase_route(
            project,
            phase,
            agent="codex",
            phase_settings=PhaseSettings("standard", "high", 10),
        )
        assert route.prompt == settings.prompts[phase]
        assert route.prompt != NATIVE_PROMPT
        assert driver.default_prompt(phase) == NATIVE_PROMPT
