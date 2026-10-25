from __future__ import annotations

import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DECLARED_MODULES = (
    "ovcaq",
    "ovcaq.__main__",
    "ovcaq.cli",
    "ovcaq.cli_io",
    "ovcaq.runtime_cli",
    "ovcaq.supervisor_cli",
    "ovcaq.workflow_cli",
    "ovcaq.config",
    "ovcaq.paths",
    "ovcaq.errors",
    "ovcaq.workflow_client",
    "ovcaq.state",
    "ovcaq.state.schema",
    "ovcaq.state.store",
    "ovcaq.state.paths",
    "ovcaq.state.commands",
    "ovcaq.workflow",
    "ovcaq.workflow.paths",
    "ovcaq.workflow.transitions",
    "ovcaq.workflow.selection",
    "ovcaq.workflow.frontmatter",
    "ovcaq.workflow.resume",
    "ovcaq.workflow.policy",
    "ovcaq.workflow.records",
    "ovcaq.workflow._files",
    "ovcaq.workflow._rename",
    "ovcaq.workflow.reports",
    "ovcaq.runtime",
    "ovcaq.runtime.supervisor",
    "ovcaq.runtime.decision",
    "ovcaq.runtime.registry",
    "ovcaq.runtime.process",
    "ovcaq.runtime._group_anchor",
    "ovcaq.runtime.watchdog",
    "ovcaq.runtime.capability",
    "ovcaq.runtime.session",
    "ovcaq.runtime._retention",
    "ovcaq.runtime._run_observation",
    "ovcaq.runtime._session_evidence",
    "ovcaq.runtime._session_io",
    "ovcaq.drivers",
    "ovcaq.drivers.base",
    "ovcaq.drivers.claude",
    "ovcaq.drivers.claude_events",
    "ovcaq.drivers.codex",
    "ovcaq.drivers.codex_events",
    "ovcaq.drivers.command",
    "ovcaq.drivers.edge",
    "ovcaq.events",
    "ovcaq.events.model",
    "ovcaq.events.reducer",
    "ovcaq.events.tail",
    "ovcaq.tui",
    "ovcaq.tui.app",
    "ovcaq.tui.discovery",
    "ovcaq.tui.model",
    "ovcaq.tui.panels",
    "ovcaq.provision",
    "ovcaq.provision.manifest",
    "ovcaq.provision.reconcile",
    "ovcaq.provision.claude",
    "ovcaq.provision.codex",
)

PACKAGE_BOUNDARIES = frozenset(
    {
        "ovcaq",
        "ovcaq.state",
        "ovcaq.workflow",
        "ovcaq.runtime",
        "ovcaq.drivers",
        "ovcaq.events",
        "ovcaq.tui",
        "ovcaq.provision",
    }
)


def _module_member(module_name: str) -> str:
    parts = module_name.split(".")
    if module_name in PACKAGE_BOUNDARIES:
        return "/".join((*parts, "__init__.py"))
    return "/".join((*parts[:-1], f"{parts[-1]}.py"))


DECLARED_PACKAGE_MEMBERS = frozenset(map(_module_member, DECLARED_MODULES))
DECLARED_RESOURCE_MEMBERS = frozenset({"ovcaq/resources/extensions.toml"})


@dataclass(frozen=True)
class BuiltArtifacts:
    wheel: Path
    sdist: Path
    version: str


@dataclass(frozen=True)
class InstalledWheel:
    root: Path
    python: Path
    console_script: Path
    environment: dict[str, str]


def assert_installed(
    origins: dict[str, str], installed: InstalledWheel, required_module: str
) -> None:
    assert required_module in origins
    for module, filename in origins.items():
        path = Path(filename).resolve()
        assert path.is_relative_to(installed.root.resolve()), (module, filename)
        assert "site-packages" in path.parts, (module, filename)


def identity(path: Path) -> list[int]:
    value = path.stat()
    return [value.st_dev, value.st_ino]


def initialize_installed_state(
    installed: InstalledWheel,
    tmp_path: Path,
    script: str,
    prd: str,
    required_module: str,
) -> tuple[Path, Path]:
    project = tmp_path / "project"
    state = project / "independent/state.json"
    project.mkdir()
    result = run_checked(
        [installed.python, "-I", "-c", script, project, state, prd],
        cwd=project,
        env=installed.environment,
    )
    assert_installed(json.loads(result.stdout), installed, required_module)
    return project, state


def command_text(command: list[str | os.PathLike[str]]) -> str:
    return shlex.join(str(part) for part in command)


def run_checked(
    command: list[str | os.PathLike[str]],
    *,
    cwd: Path,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [str(part) for part in command],
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0:
        pytest.fail(
            f"command failed ({result.returncode}): {command_text(command)}\n"
            f"cwd: {cwd}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def isolated_environment(sandbox_root: Path) -> dict[str, str]:
    sandbox_root.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    for inherited_name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        environment.pop(inherited_name, None)
    environment.update(
        {
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_INDEX": "1",
            "PYTHONNOUSERSITE": "1",
            "UV_CACHE_DIR": str(sandbox_root / "uv-cache"),
            "UV_NO_PROGRESS": "1",
            "UV_OFFLINE": "1",
            "UV_PYTHON_DOWNLOADS": "never",
            "XDG_CACHE_HOME": str(sandbox_root / "xdg-cache"),
            "XDG_CONFIG_HOME": str(sandbox_root / "xdg-config"),
            "XDG_STATE_HOME": str(sandbox_root / "xdg-state"),
        }
    )
    return environment


def _run(
    command: list[str | Path],
    *,
    cwd: Path,
    installed_wheel: InstalledWheel,
) -> subprocess.CompletedProcess[str]:
    result = _run_unchecked(command, cwd=cwd, installed_wheel=installed_wheel)
    assert result.returncode == 0, (
        f"installed command failed ({result.returncode}): {command_text(command)}\n"
        f"cwd: {cwd}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    return result


def _run_unchecked(
    command: list[str | Path],
    *,
    cwd: Path,
    installed_wheel: InstalledWheel,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(part) for part in command],
        cwd=cwd,
        env=installed_wheel.environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _hostile_cwd(tmp_path: Path) -> Path:
    cwd = tmp_path / "arbitrary-cwd"
    decoy = cwd / "cli"
    decoy.mkdir(parents=True)
    (decoy / "__init__.py").write_text(
        "raise RuntimeError('checkout-relative cli import reached decoy')\n",
        encoding="utf-8",
    )
    return cwd


def _installed_workflow_root(installed_wheel: InstalledWheel, tmp_path: Path) -> Path:
    root = _hostile_cwd(tmp_path)
    _run(
        [installed_wheel.console_script, "--root", root, "--json", "init"],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    script = """
import sys
from pathlib import Path
from ovcaq.paths import state_path
from ovcaq.state.store import StateStore
root = Path(sys.argv[1])
def start(state):
    state["batch"].update({
        "id": "installed-batch", "status": "running",
        "started_at": "2026-09-05T10:00:00Z",
    })
    state["work"]["prd"] = "00004-workflow-core-v1.md"
    state["work"]["tasks_total"] = 1
    state["tasks"] = [{
        "id": 1, "name": "pending", "description": "retained work",
        "active_form": "working", "status": "pending", "blocked_by": [],
        "tier": None, "files_touched": None, "public_contract_edit": None,
        "estimates": {"input_tokens": None, "context_peak": None},
        "attempts": [], "metadata": {},
    }]
StateStore(state_path(root)).transaction(start)
wip = root / "docs/dev/project-management/prds/wip"
wip.mkdir(parents=True)
wip.joinpath("00004-workflow-core-v1.md").write_text("# Workflow\\n", encoding="utf-8")
"""
    _run(
        [installed_wheel.python, "-c", script, root],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    return root


def workflow_command(
    installed: InstalledWheel, root: Path, command: str, *args: str | Path
) -> list[str | Path]:
    return [
        installed.console_script,
        "--root",
        root,
        "--json",
        "workflow",
        command,
        *args,
    ]


def stall_command(
    installed: InstalledWheel, root: Path, *, site: str, detail: str
) -> list[str | Path]:
    return workflow_command(
        installed,
        root,
        "stall",
        "--prd",
        "00004-workflow-core-v1.md",
        "--site",
        site,
        "--detail",
        detail,
    )
