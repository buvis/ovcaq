from __future__ import annotations

import ast
import json
import shutil
import subprocess
import sys
from pathlib import Path

from tests.workflow_client.test_transport import (
    BUNDLE,
    FAKE_CONTROLLER,
    FakeController,
    make_client,
)

ROOT = Path(__file__).parents[2]
CLIENT_SOURCES = (
    ROOT / "src" / "ovcaq" / "workflow_client.py",
    ROOT / "tools" / "autopilot-prerequisites",
)
FORBIDDEN_IMPORT_PARTS = {"agent_plugins", "autopilot", "plugins"}
FORBIDDEN_TEXT = ("sys.path", "importlib", ".claude/plugins", "agent-plugins")
RUNTIME_PROBE = """\
import json
import sys

before = list(sys.path)
import ovcaq.config
import ovcaq.workflow_client

files = sorted(
    file
    for module in list(sys.modules.values())
    if (file := getattr(module, "__file__", None))
)
print(json.dumps({"files": files, "before": before, "after": list(sys.path)}))
"""


def test_controller_contract_fixtures(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle" / "controller-v1.json"
    bundle.parent.mkdir()
    shutil.copyfile(BUNDLE, bundle)
    project_root = tmp_path / "project"
    project_root.mkdir()
    script = tmp_path / "controller.py"
    script.write_text(FAKE_CONTROLLER, encoding="utf-8")
    fake = FakeController(script, tmp_path / "spec.json", tmp_path / "calls.log")
    fake.respond(bundle.read_bytes().decode("utf-8"))
    data = json.loads(bundle.read_text(encoding="utf-8"))

    contract = make_client(fake, project_root, bundle=bundle).contract()

    assert contract.protocol_major == data["protocol_major"]
    assert contract.package_version == data["package_version"]
    assert contract.schema_digest == data["schema_digest"]
    assert contract.fixture_digest == data["fixture_digest"]
    assert contract.operations == frozenset(data["operations"])
    assert contract.capabilities == frozenset(data["capabilities"])
    [call] = fake.calls()
    assert call["argv"] == [*fake.child_argv, "--json", "contract"]


def imported_modules(source: str) -> list[str]:
    names: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names.extend(f"{module}.{alias.name}" for alias in node.names)
    return names


def test_no_plugin_import() -> None:
    for path in CLIENT_SOURCES:
        source = path.read_text(encoding="utf-8")
        modules = imported_modules(source)

        assert modules, path
        for module in modules:
            top = module.split(".")[0]
            assert top in sys.stdlib_module_names or top == "ovcaq", (path, module)
            assert not FORBIDDEN_IMPORT_PARTS & set(module.split(".")), (path, module)
        for text in FORBIDDEN_TEXT:
            assert text not in source, (path, text)


def test_no_plugin_import_at_runtime(tmp_path: Path) -> None:
    completed = subprocess.run(
        [sys.executable, "-c", RUNTIME_PROBE],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    probe = json.loads(completed.stdout)

    assert any(file.endswith("workflow_client.py") for file in probe["files"])
    for file in probe["files"]:
        assert ".claude/plugins/" not in file
        assert "agent-plugins" not in file
    assert probe["after"] == probe["before"]
