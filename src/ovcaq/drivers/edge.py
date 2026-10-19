"""Provider edge: construct the configured built-in driver."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from ovcaq.config import AgentSettings, agent_settings
from ovcaq.drivers.base import AgentDriver, LaunchRequest, LaunchSpec
from ovcaq.drivers.claude import ClaudeDriver
from ovcaq.drivers.codex import CodexDriver
from ovcaq.errors import CommandError, ErrorCode


def _map_model_to_tier(
    settings: AgentSettings, request: LaunchRequest
) -> LaunchRequest:
    tiers = {model: tier for tier, model in settings.tiers.items()}
    if request.model in tiers:
        return replace(request, model=tiers[request.model])
    return request


class _ResolvedModelClaudeDriver(ClaudeDriver):
    """Map the supervisor's resolved model back to its configured tier key."""

    def build_launch(self, request: LaunchRequest) -> LaunchSpec:
        return super().build_launch(_map_model_to_tier(self._settings, request))


class _ResolvedModelCodexDriver(CodexDriver):
    """Map the supervisor's resolved model back to its configured tier key."""

    def build_launch(self, request: LaunchRequest) -> LaunchSpec:
        return super().build_launch(_map_model_to_tier(self._settings, request))


def build_driver(root: Path, name: str | None) -> AgentDriver:
    agent = agent_settings(root, name=name)
    if agent.name == "claude":
        return _ResolvedModelClaudeDriver(agent, run_id=uuid4().hex)
    if agent.name == "codex":
        return _ResolvedModelCodexDriver(agent, run_id=uuid4().hex)
    raise CommandError(ErrorCode.RUNTIME_FORMAT, f"unknown agent: {agent.name}")
