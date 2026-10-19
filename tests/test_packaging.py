from __future__ import annotations

import re
import subprocess
import tarfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_PRODUCTION_PATTERNS = {
    "external checkout path": re.compile(rb"/" rb"Users/[^/]+/git/src/github\.com/"),
    "sys.path bootstrap": re.compile(
        rb"\bsys\.path\s*\.\s*(?:append|extend|insert)\s*\("
    ),
    "live-home fixture access": re.compile(
        rb"(?:Path\.home\(\)|expanduser\([^)]*\)|"
        rb"(?:os\.)?environ(?:\.get\([^)]*['\"]HOME['\"][^)]*\)"
        rb"|\[\s*['\"]HOME['\"]\s*\]))[\s\S]{0,256}"
        rb"['\"]\.claude['\"]"
    ),
    "run-autopilot home literal": re.compile(
        rb"~[/\\]\.claude[/\\]skills[/\\]run-autopilot"
    ),
}


def _assert_portable_package(sources: dict[str, bytes]) -> None:
    failures = [
        f"{name}: {description}"
        for name, content in sources.items()
        for description, pattern in FORBIDDEN_PRODUCTION_PATTERNS.items()
        if pattern.search(content)
    ]
    assert failures == []


def test_package_source_has_no_checkout_bootstrap_or_live_home_dependency() -> None:
    package_root = PROJECT_ROOT / "src" / "ovcaq"
    sources = {
        path.relative_to(PROJECT_ROOT).as_posix(): path.read_bytes()
        for path in package_root.rglob("*.py")
    }

    assert sources
    _assert_portable_package(sources)


@pytest.fixture(scope="module")
def source_distribution(tmp_path_factory: pytest.TempPathFactory) -> Path:
    distribution = tmp_path_factory.mktemp("packaging-audit")
    build = subprocess.run(
        ["uv", "build", "--sdist", "--out-dir", str(distribution)],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert build.returncode == 0, (
        f"source distribution build failed ({build.returncode})\n"
        f"stdout:\n{build.stdout}\nstderr:\n{build.stderr}"
    )
    archives = tuple(distribution.glob("*.tar.gz"))
    assert len(archives) == 1
    return archives[0]


def test_source_distribution_has_no_checkout_bootstrap_or_live_home_dependency(
    source_distribution: Path,
) -> None:
    with tarfile.open(source_distribution, "r:gz") as archive:
        sources = {
            member.name: extracted.read()
            for member in archive.getmembers()
            if member.isfile() and "/src/ovcaq/" in member.name
            if (extracted := archive.extractfile(member)) is not None
        }

    assert sources
    _assert_portable_package(sources)
