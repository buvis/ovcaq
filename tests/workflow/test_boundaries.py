from __future__ import annotations

import ast
from pathlib import Path

WORKFLOW_ROOT = Path("src/ovcaq/workflow")
FORBIDDEN_IMPORT_PREFIXES = (
    "ovcaq.drivers",
    "ovcaq.events",
    "ovcaq.provision",
    "ovcaq.runtime",
    "ovcaq.tui",
)
FORBIDDEN_STRINGS = (
    "anthropic",
    "claude",
    "codex",
    "qwen",
    "docs/dev/project-management/autopilot",
    ".claude",
    ".codex",
)
FORBIDDEN_SKILL_COMMANDS = (
    "/run-autopilot",
    "/review-work-completion",
    "/work",
)


def test_workflow_imports_only_state_workflow_and_standard_library() -> None:
    violations: list[str] = []
    for path in sorted(WORKFLOW_ROOT.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: tuple[str, ...] = ()
            if isinstance(node, ast.Import):
                names = tuple(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                names = (node.module,)
            for name in names:
                if name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                    violations.append(f"{path}:{node.lineno}: {name}")
    assert violations == []


def test_workflow_contains_no_provider_or_legacy_runtime_strings() -> None:
    violations: list[str] = []
    for path in sorted(WORKFLOW_ROOT.glob("*.py")):
        text = path.read_text(encoding="utf-8").lower()
        for forbidden in FORBIDDEN_STRINGS:
            if forbidden in text:
                violations.append(f"{path}: {forbidden}")
    assert violations == []


def test_workflow_contains_no_external_skill_commands() -> None:
    violations: list[str] = []
    for path in sorted(WORKFLOW_ROOT.glob("*.py")):
        text = path.read_text(encoding="utf-8").lower()
        for command in FORBIDDEN_SKILL_COMMANDS:
            if command in text:
                violations.append(f"{path}: {command}")
    assert violations == []
