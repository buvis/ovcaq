from __future__ import annotations

import os
import shutil
import sys
import zipfile
from email.parser import Parser

import pytest
from packaging_support import (
    PROJECT_ROOT,
    BuiltArtifacts,
    InstalledWheel,
    isolated_environment,
    run_checked,
)


@pytest.fixture(scope="session")
def built_artifacts(tmp_path_factory: pytest.TempPathFactory) -> BuiltArtifacts:
    temp_root = tmp_path_factory.mktemp("ovcaq-distributions")
    output_dir = temp_root / "dist"
    output_dir.mkdir()
    environment = isolated_environment(temp_root / "sandbox")
    uv = shutil.which("uv")
    if uv is None:
        pytest.fail("build command unavailable: uv")

    run_checked(
        [
            uv,
            "--no-config",
            "build",
            "--offline",
            "--no-build-isolation",
            "--no-cache",
            "--no-progress",
            "--sdist",
            "--wheel",
            "--out-dir",
            output_dir,
            PROJECT_ROOT,
        ],
        cwd=PROJECT_ROOT,
        env=environment,
    )

    wheels = tuple(output_dir.glob("*.whl"))
    sdists = tuple(output_dir.glob("*.tar.gz"))
    assert len(wheels) == 1, f"build produced unexpected wheels: {wheels!r}"
    assert len(sdists) == 1, f"build produced unexpected sdists: {sdists!r}"

    with zipfile.ZipFile(wheels[0]) as wheel:
        metadata_members = [
            name for name in wheel.namelist() if name.endswith(".dist-info/METADATA")
        ]
        assert len(metadata_members) == 1, (
            f"{wheels[0].name}: expected one METADATA member, "
            f"found {metadata_members!r}"
        )
        metadata = Parser().parsestr(wheel.read(metadata_members[0]).decode("utf-8"))
    version = metadata.get("Version")
    assert version, f"{wheels[0].name}:{metadata_members[0]} has no Version"

    return BuiltArtifacts(wheel=wheels[0], sdist=sdists[0], version=version)


@pytest.fixture(scope="session")
def installed_wheel(
    built_artifacts: BuiltArtifacts,
    tmp_path_factory: pytest.TempPathFactory,
) -> InstalledWheel:
    temp_root = tmp_path_factory.mktemp("ovcaq-installed-wheel")
    environment = isolated_environment(temp_root / "sandbox")
    venv_root = temp_root / "venv"

    run_checked(
        [sys.executable, "-m", "venv", "--without-pip", venv_root],
        cwd=temp_root,
        env=environment,
    )

    scripts_dir = venv_root / ("Scripts" if os.name == "nt" else "bin")
    python = scripts_dir / ("python.exe" if os.name == "nt" else "python")
    console_script = scripts_dir / ("ovcaq.exe" if os.name == "nt" else "ovcaq")
    uv = shutil.which("uv")
    if uv is None:
        pytest.fail("wheel install command unavailable: uv")
    run_checked(
        [
            uv,
            "--no-config",
            "pip",
            "install",
            "--offline",
            "--no-cache",
            "--no-index",
            "--no-deps",
            "--no-build",
            "--python",
            python,
            built_artifacts.wheel,
        ],
        cwd=temp_root,
        env=environment,
    )
    environment["PATH"] = os.pathsep.join(
        (str(scripts_dir), environment.get("PATH", ""))
    )
    assert console_script.is_file(), (
        f"{built_artifacts.wheel.name}: missing installed console script "
        f"{console_script}"
    )
    return InstalledWheel(
        root=venv_root,
        python=python,
        console_script=console_script,
        environment=environment,
    )
