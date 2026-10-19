"""Source guards: the TUI observes shared services and never re-implements them."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

TUI = Path(__file__).resolve().parents[2] / "src/ovcaq/tui"
MODULES = tuple(sorted(TUI.glob("*.py")))

PROVIDER_MARKERS = (
    "anthropic",
    "claude",
    "codex",
    "openai",
    "gemini",
    "haiku",
    "opus",
    "sonnet",
    "gpt-",
    "stream-json",
    "content_block",
    "rate_limit",
)
# Modules whose use means probing, locking, signalling or provider/workflow logic.
BANNED_IMPORTS = (
    "subprocess",
    "fcntl",
    "psutil",
    "signal",
    "ovcaq.drivers",
    "ovcaq.provision",
    "ovcaq.workflow",
)
BANNED_CALLS = {"os.kill", "os.killpg", "os.system", "os.popen"}
LOCK_CALLS = {"flock", "lockf"}
PROBE_COMMANDS = {"ps", "/bin/ps", "/usr/bin/ps", "pgrep", "lsof"}
# Definitions that would duplicate a shared service (calls and imports stay legal).
DUPLICATE_NAME_PARTS = (
    "registry",
    "liveness",
    "lock",
    "alive",
    "process_identity",
    "process_match",
    "transition",
)
TRANSITION_METHODS = {
    "transaction",
    "add_task",
    "start_task",
    "complete_task",
    "append_attempt",
    "set_task_body",
    "set_task_meta",
    "set_task_status",
    "clear_tasks",
    "set_contract_card",
    "restore",
    "initialize",
}
STATE_SECTIONS = {"work", "control", "batch", "tasks", "review", "recovery", "revision"}


def _dotted(node: ast.expr) -> str:
    if isinstance(node, ast.Attribute):
        return f"{_dotted(node.value)}.{node.attr}"
    return node.id if isinstance(node, ast.Name) else ""


def _imported(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def _call_violations(node: ast.Call) -> list[str]:
    callee = _dotted(node.func)
    tail = callee.rpartition(".")[2]
    found = []
    if callee in BANNED_CALLS or tail in LOCK_CALLS:
        found.append(f"calls {callee}")
    if isinstance(node.func, ast.Attribute) and tail in TRANSITION_METHODS:
        found.append(f"mutates state via {callee}")
    return found


def _written_sections(node: ast.Subscript) -> list[str]:
    """State sections named anywhere in a subscript chain that is stored to."""
    sections = []
    current: ast.expr = node
    while isinstance(current, ast.Subscript):
        key = current.slice
        if isinstance(key, ast.Constant) and key.value in STATE_SECTIONS:
            sections.append(key.value)
        current = current.value
    return sections


def violations(source: str) -> list[str]:
    """Return one line per construct that duplicates a shared service."""
    tree = ast.parse(source)
    found = [
        f"imports {name}"
        for name in _imported(tree)
        for banned in BANNED_IMPORTS
        if name == banned or name.startswith(f"{banned}.")
    ]
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            found.extend(_call_violations(node))
        elif isinstance(node, ast.Constant) and node.value in PROBE_COMMANDS:
            found.append(f"probes with {node.value!r}")
        elif isinstance(node, ast.Subscript) and not isinstance(node.ctx, ast.Load):
            found.extend(
                f"writes state section {section!r}"
                for section in _written_sections(node)
            )
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            folded = node.name.casefold()
            if any(part in folded for part in DUPLICATE_NAME_PARTS):
                found.append(f"defines {node.name}")
    return found


def test_scan_covers_the_tui_package() -> None:
    assert {"app.py", "discovery.py", "model.py", "panels.py"} <= {
        module.name for module in MODULES
    }


@pytest.mark.parametrize("module", MODULES, ids=lambda module: module.name)
def test_tui_module_has_no_provider_native_identifiers(module: Path) -> None:
    folded = module.read_text(encoding="utf-8").casefold()
    assert [marker for marker in PROVIDER_MARKERS if marker in folded] == []


@pytest.mark.parametrize("module", MODULES, ids=lambda module: module.name)
def test_tui_module_does_not_duplicate_shared_services(module: Path) -> None:
    assert violations(module.read_text(encoding="utf-8")) == []


def test_tui_consumes_the_shared_services_it_must_not_reimplement() -> None:
    tree = ast.parse((TUI / "app.py").read_text(encoding="utf-8"))
    imported = {
        (node.module, alias.name)
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert {
        ("ovcaq.runtime.registry", "FleetRegistry"),
        ("ovcaq.supervisor_cli", "verify_run"),
        ("ovcaq.supervisor_cli", "stop_supervisor"),
        ("ovcaq.state.commands", "StateService"),
        ("ovcaq.tui.discovery", "discover_fleet"),
    } <= imported


def test_guard_allows_imports_and_calls_of_shared_services() -> None:
    source = (
        "from ovcaq.runtime.registry import FleetRegistry, process_matches\n"
        "from ovcaq.runtime.session import observe_run\n"
        "from ovcaq.supervisor_cli import stop_supervisor, verify_run\n"
        "def poll(registry, service, run, notice):\n"
        "    live = registry.snapshot().live\n"
        "    verify_run(run, registry)\n"
        "    process_matches(run)\n"
        "    observe_run(run)\n"
        "    service.request_pause(notice)\n"
        "    service.resume()\n"
        "    stop_supervisor(run)\n"
        "    return live, {'work': 1}['work']\n"
    )
    assert violations(source) == []


@pytest.mark.parametrize(
    "source,expected",
    [
        ("import subprocess\n", "imports subprocess"),
        ("import subprocess\nsubprocess.run(['ps', '-p', '1'])\n", "probes with 'ps'"),
        ("from ovcaq.drivers.edge import build_driver\n", "imports ovcaq.drivers.edge"),
        ("from ovcaq.workflow import transitions\n", "imports ovcaq.workflow"),
        ("import os\nos.kill(1, 0)\n", "calls os.kill"),
        ("import fcntl\nfcntl.flock(3, 2)\n", "calls fcntl.flock"),
        ("def run_lock_held(path): ...\n", "defines run_lock_held"),
        ("class FleetRegistry: ...\n", "defines FleetRegistry"),
        ("def process_identity(pid): ...\n", "defines process_identity"),
        ("def is_alive(pid): ...\n", "defines is_alive"),
        ("store.transaction(lambda s: None)\n", "mutates state via store.transaction"),
        ("service.start_task(1)\n", "mutates state via service.start_task"),
        ("state['work']['phase'] = 'done'\n", "writes state section 'work'"),
        ("def next_transition(state): ...\n", "defines next_transition"),
    ],
)
def test_guard_rejects_duplicate_implementations(source: str, expected: str) -> None:
    assert expected in violations(source)
