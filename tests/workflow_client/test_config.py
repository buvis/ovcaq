from __future__ import annotations

import json
import shutil
from dataclasses import fields
from pathlib import Path

import pytest

from ovcaq.config import (
    ConfigurationError,
    WorkflowSettings,
    controller_settings,
    workflow_settings,
)
from ovcaq.workflow_client import ControllerConfig

BUNDLE = Path(__file__).parents[1] / "fixtures" / "workflow" / "controller-v1.json"


@pytest.fixture
def config_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "user-config"))
    root = tmp_path / "project"
    root.mkdir()
    return root


def write_project_config(root: Path, text: str) -> None:
    (root / "ovcaq.toml").write_text(text, encoding="utf-8")


def install_bundle(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    bundle = directory / "controller-v1.json"
    shutil.copyfile(BUNDLE, bundle)
    return bundle


def toml_value(value: object) -> str:
    """Render a string or list of strings; JSON's forms are valid TOML."""
    return json.dumps(value)


# controller_settings


@pytest.mark.parametrize(
    "declaration",
    [
        None,
        "",
        "version = 1\n",
        '[workflow]\nprd_root = "requirements"\n',
        "[workflow]\ncontract_bundle = {bundle}\nactor_file = {actor}\n",
    ],
    ids=["no-file", "empty-file", "no-workflow", "other-keys", "no-argv"],
)
def test_controller_settings_is_opt_in_on_controller_argv(
    config_root: Path, tmp_path: Path, declaration: str | None
) -> None:
    bundle = install_bundle(tmp_path / "bundles")
    if declaration is not None:
        write_project_config(
            config_root,
            declaration.format(
                bundle=toml_value(str(bundle)),
                actor=toml_value(str(tmp_path / "actor.json")),
            ),
        )

    assert controller_settings(config_root) is None


def test_controller_settings_resolves_relative_paths_against_project_root(
    config_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = install_bundle(config_root / "bundles")
    actor = config_root / "actors" / "actor.json"
    actor.parent.mkdir()
    actor.write_text("{}", encoding="utf-8")
    write_project_config(
        config_root,
        '[workflow]\ncontroller_argv = ["autopilot-controller"]\n'
        'contract_bundle = "bundles/controller-v1.json"\n'
        'actor_file = "actors/actor.json"\n',
    )
    # Run from elsewhere so cwd-relative resolution cannot pass by accident.
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    config = controller_settings(config_root)

    assert config is not None
    assert config.contract_bundle == bundle
    assert config.contract_bundle == config_root / "bundles" / "controller-v1.json"
    assert config.actor_file == config_root / "actors" / "actor.json"


@pytest.mark.parametrize(
    "argv",
    [["autopilot-controller"], ["uvx", "autopilot-controller", "--profile", "ci"]],
    ids=["single", "multiple"],
)
def test_controller_settings_builds_config_from_workflow_table(
    config_root: Path, tmp_path: Path, argv: list[str]
) -> None:
    bundle = install_bundle(tmp_path / f"bundles-{len(argv)}")
    actor = tmp_path / f"actor-{len(argv)}.json"
    actor.write_text("{}", encoding="utf-8")
    write_project_config(
        config_root,
        "[workflow]\n"
        f"controller_argv = {toml_value(argv)}\n"
        f"contract_bundle = {toml_value(str(bundle))}\n"
        f"actor_file = {toml_value(str(actor))}\n",
    )

    config = controller_settings(config_root)

    assert isinstance(config, ControllerConfig)
    assert config.argv == tuple(argv)
    assert config.contract_bundle == bundle
    assert config.actor_file == actor
    assert config.project_root == config_root


@pytest.mark.parametrize(
    "value",
    [
        '"autopilot-controller"',
        "[]",
        "[1, 2]",
        '["autopilot-controller", 3]',
        '[["autopilot-controller"]]',
        "12",
    ],
    ids=["bare-string", "empty", "ints", "mixed", "nested", "int"],
)
def test_controller_settings_rejects_malformed_controller_argv(
    config_root: Path, tmp_path: Path, value: str
) -> None:
    bundle = install_bundle(tmp_path / "bundles")
    write_project_config(
        config_root,
        f"[workflow]\ncontroller_argv = {value}\n"
        f"contract_bundle = {toml_value(str(bundle))}\n",
    )

    with pytest.raises(ConfigurationError):
        controller_settings(config_root)


@pytest.mark.parametrize(
    "bundle_line",
    [
        'contract_bundle = "missing/controller-v1.json"\n',
        "contract_bundle = {absent}\n",
        "",
        "contract_bundle = 12\n",
    ],
    ids=["relative-missing", "absolute-missing", "absent-key", "wrong-type"],
)
def test_controller_settings_rejects_unusable_contract_bundle(
    config_root: Path, tmp_path: Path, bundle_line: str
) -> None:
    absent = tmp_path / "bundles" / "controller-v1.json"
    write_project_config(
        config_root,
        '[workflow]\ncontroller_argv = ["autopilot-controller"]\n'
        + bundle_line.format(absent=toml_value(str(absent))),
    )

    with pytest.raises(ConfigurationError):
        controller_settings(config_root)


@pytest.mark.parametrize("value", ["12", '["actor.json"]'], ids=["int", "list"])
def test_controller_settings_rejects_malformed_actor_file(
    config_root: Path, tmp_path: Path, value: str
) -> None:
    bundle = install_bundle(tmp_path / "bundles")
    write_project_config(
        config_root,
        '[workflow]\ncontroller_argv = ["autopilot-controller"]\n'
        f"contract_bundle = {toml_value(str(bundle))}\n"
        f"actor_file = {value}\n",
    )

    with pytest.raises(ConfigurationError):
        controller_settings(config_root)


# WorkflowSettings stays additive


def test_workflow_settings_fields_extend_the_original_shape() -> None:
    assert [field.name for field in fields(WorkflowSettings)] == [
        "prd_root",
        "runtime_root",
        "state_file",
        "available_tiers",
        "controller_argv",
        "contract_bundle",
        "actor_file",
    ]


def test_workflow_settings_positional_construction_defaults_controller_fields(
    tmp_path: Path,
) -> None:
    settings = WorkflowSettings(
        tmp_path / "prds",
        tmp_path / "runtime",
        tmp_path / "runtime" / "state.json",
        frozenset({"fast"}),
    )

    assert settings.prd_root == tmp_path / "prds"
    assert settings.available_tiers == {"fast"}
    assert settings.controller_argv is None
    assert settings.contract_bundle is None
    assert settings.actor_file is None


@pytest.mark.parametrize("source", ["default", "configured"])
def test_workflow_settings_without_controller_keys_is_unchanged(
    config_root: Path, source: str
) -> None:
    if source == "default":
        prd_root = config_root / "docs/dev/project-management/prds"
        runtime_root = config_root / "docs/dev/project-management/ovcaq"
        state_file = runtime_root / "state.json"
    else:
        prd_root = config_root / "requirements"
        runtime_root = config_root / "private"
        state_file = runtime_root / "workflow.json"
        write_project_config(
            config_root,
            "[workflow]\n"
            f"prd_root = {toml_value(str(prd_root))}\n"
            f"runtime_root = {toml_value(str(runtime_root))}\n"
            f"state_file = {toml_value(str(state_file))}\n",
        )

    settings = workflow_settings(config_root)

    assert settings.prd_root == prd_root
    assert settings.runtime_root == runtime_root
    assert settings.state_file == state_file
    assert settings.available_tiers == frozenset()
    assert settings.controller_argv is None
    assert settings.contract_bundle is None
    assert settings.actor_file is None
