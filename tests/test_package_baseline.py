from __future__ import annotations

import importlib
import subprocess
import sys
from collections.abc import Sequence
from importlib import metadata, resources
from pathlib import Path

import pytest

PACKAGE_MODULES = (
    "ovcaq",
    "ovcaq.__main__",
    "ovcaq.cli",
    "ovcaq.config",
    "ovcaq.paths",
    "ovcaq.errors",
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
    "ovcaq.workflow.reports",
    "ovcaq.runtime",
    "ovcaq.runtime.supervisor",
    "ovcaq.runtime.decision",
    "ovcaq.runtime.registry",
    "ovcaq.runtime.process",
    "ovcaq.runtime.watchdog",
    "ovcaq.runtime.capability",
    "ovcaq.runtime.session",
    "ovcaq.drivers",
    "ovcaq.drivers.base",
    "ovcaq.drivers.claude",
    "ovcaq.drivers.codex",
    "ovcaq.drivers.command",
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


@pytest.mark.parametrize("module_name", PACKAGE_MODULES)
def test_declared_package_boundary_imports(module_name: str) -> None:
    module = importlib.import_module(module_name)
    module_file = Path(module.__file__)
    expected_path = module_name.split(".")
    if hasattr(module, "__path__"):
        expected_path.append("__init__.py")
    else:
        expected_path[-1] = f"{expected_path[-1]}.py"

    assert module.__name__ == module_name
    assert module.__spec__ is not None
    assert module.__spec__.origin == module.__file__
    assert module_file.is_file()
    assert module_file.parts[-len(expected_path) :] == tuple(expected_path)


def test_package_exposes_development_version() -> None:
    import ovcaq

    assert ovcaq.__version__ == "0.1.0.dev0"
    assert ovcaq.__version__ == metadata.version("ovcaq")


def test_package_includes_extensions_manifest_resource() -> None:
    manifest = resources.files("ovcaq").joinpath("resources/extensions.toml")

    assert manifest.is_file()


def _main_exit_code(argv: Sequence[str]) -> int:
    from ovcaq.cli import main

    try:
        return main(argv)
    except SystemExit as error:
        assert isinstance(error.code, int)
        return error.code


@pytest.mark.parametrize("help_flag", ("--help", "-h"))
def test_console_script_callable_prints_ovcaq_help_and_usage(
    help_flag: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = _main_exit_code((help_flag,))
    captured = capsys.readouterr()
    help_text = captured.out + captured.err

    assert exit_code == 0
    assert "OVCAQ" in help_text.upper()
    assert "usage:" in help_text.lower()


def test_module_execution_prints_ovcaq_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "ovcaq", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "OVCAQ" in (result.stdout + result.stderr).upper()


def test_unsupported_product_command_fails(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = _main_exit_code(("launch",))
    captured = capsys.readouterr()
    diagnostic = captured.out + captured.err

    assert exit_code != 0
    assert "usage:" in diagnostic.lower()
    assert "invalid choice: 'launch'" in diagnostic
