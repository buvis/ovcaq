from __future__ import annotations

import base64
import csv
import hashlib
import io
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import zipfile
from collections import Counter
from collections.abc import Iterator
from configparser import ConfigParser
from email.parser import Parser
from pathlib import Path, PurePosixPath

from packaging.version import InvalidVersion, Version
from packaging_support import (
    DECLARED_PACKAGE_MEMBERS,
    DECLARED_RESOURCE_MEMBERS,
    PROJECT_ROOT,
    BuiltArtifacts,
    isolated_environment,
    run_checked,
)

ROOT_METADATA = frozenset(
    {
        ".gitignore",
        "CHANGELOG.md",
        "LICENSE",
        "README.md",
        "pyproject.toml",
        "uv.lock",
    }
)
TEXT_SUFFIXES = frozenset(
    {
        ".cfg",
        ".csv",
        ".ini",
        ".json",
        ".jsonl",
        ".lock",
        ".md",
        ".py",
        ".toml",
        ".txt",
        ".yaml",
        ".yml",
    }
)
TEXT_FILENAMES = frozenset(
    {"LICENSE", "METADATA", "PKG-INFO", "RECORD", "WHEEL", "entry_points.txt"}
)
FORBIDDEN_DIRECTORY_SEGMENTS = frozenset(
    {
        ".cache",
        ".claude",
        ".codex",
        ".eggs",
        ".git",
        ".github",
        ".hg",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".svn",
        ".tox",
        ".venv",
        "__pycache__",
        "agent",
        "agents",
        "autopilot",
        "build",
        "dist",
        "hook",
        "hooks",
        "plugin",
        "plugins",
        "session",
        "sessions",
        "skill",
        "skills",
        "skills-library",
        "temp",
        "tmp",
        "transcript",
        "transcripts",
    }
)

PERSONAL_PATH_PATTERNS = (
    re.compile(re.escape("/" + "Users" + "/") + r"[^/\s]+/"),
    re.compile(re.escape("/" + "home" + "/") + r"[^/\s]+/"),
    re.compile(r"C:\\Users\\[^\\\s]+\\", re.IGNORECASE),
    re.compile(r"/root/(?:\.claude|\.codex)(?:/|\b)"),
    re.compile(r"(?:~|\$HOME|\$\{HOME\})/(?:\.claude|\.codex)(?:/|\b)"),
)
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)authorization\s*:\s*bearer\s+[A-Za-z0-9._~+/-]{20,}"),
    re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)"
        r"\s*[:=]\s*[\"']?[A-Za-z0-9/+_.-]{24,}"
    ),
)


def _wheel_files(wheel_path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(wheel_path) as archive:
        return {
            member.filename: archive.read(member)
            for member in archive.infolist()
            if not member.is_dir()
        }


def _sdist_files(sdist_path: Path) -> dict[str, bytes]:
    with tarfile.open(sdist_path, mode="r:gz") as archive:
        unsafe_paths = [
            member.name
            for member in archive.getmembers()
            if PurePosixPath(member.name).is_absolute()
            or ".." in PurePosixPath(member.name).parts
            or "\\" in member.name
        ]
        assert not unsafe_paths, (
            f"{sdist_path.name}: unsafe member paths: {unsafe_paths!r}"
        )
        unsupported = [
            member.name
            for member in archive.getmembers()
            if not (member.isfile() or member.isdir())
        ]
        assert not unsupported, (
            f"{sdist_path.name}: unsupported archive member types: {unsupported!r}"
        )
        members = [member for member in archive.getmembers() if member.isfile()]
        roots = {PurePosixPath(member.name).parts[0] for member in members}
        assert len(roots) == 1, (
            f"{sdist_path.name}: expected one archive root, found {sorted(roots)!r}"
        )
        root = next(iter(roots))
        files: dict[str, bytes] = {}
        for member in members:
            relative = PurePosixPath(member.name).relative_to(root).as_posix()
            extracted = archive.extractfile(member)
            assert extracted is not None, f"{sdist_path.name}:{member.name} unreadable"
            files[relative] = extracted.read()
        return files


def _diff_message(
    artifact_name: str,
    actual: set[str],
    expected: set[str],
) -> str:
    unexpected = sorted(actual - expected)
    missing = sorted(expected - actual)
    return (
        f"{artifact_name}: distribution member mismatch\n"
        f"unexpected: {unexpected!r}\nmissing: {missing!r}"
    )


def _committed_evidence() -> set[str]:
    # pyproject excludes /docs/dev from the sdist.
    command = ["git", "ls-files", "--", "docs", "tests", ":(exclude)docs/dev"]
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"command failed ({result.returncode}): {' '.join(command)}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    return set(result.stdout.splitlines())


def _artifact_file_sets(
    built_artifacts: BuiltArtifacts,
) -> Iterator[tuple[str, dict[str, bytes]]]:
    yield built_artifacts.wheel.name, _wheel_files(built_artifacts.wheel)
    yield built_artifacts.sdist.name, _sdist_files(built_artifacts.sdist)


def _path_violation(member: str) -> str | None:
    if "\\" in member:
        return "backslash path"
    path = PurePosixPath(member)
    if path.is_absolute() or ".." in path.parts:
        return "absolute or traversing path"
    lower_parts = tuple(part.lower() for part in path.parts)
    bad_segments = sorted(set(lower_parts) & FORBIDDEN_DIRECTORY_SEGMENTS)
    if bad_segments:
        return f"forbidden content directory {bad_segments!r}"
    if any(part in {"home", "users"} for part in lower_parts):
        return "personal home path"
    if path.suffix.lower() in {".pyc", ".pyo", ".tmp"}:
        return f"forbidden generated suffix {path.suffix}"
    if any(part.endswith((".egg-info", ".dist-info.tmp")) for part in lower_parts):
        return "build output"
    if path.name.lower() in {".ds_store", "state.json", "state.json.bak"}:
        return "personal state or temporary file"
    return None


def _text_members(files: dict[str, bytes]) -> Iterator[tuple[str, str]]:
    for member, payload in files.items():
        path = PurePosixPath(member)
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in TEXT_FILENAMES:
            continue
        yield member, payload.decode("utf-8", errors="replace")


def test_wheel_contains_exact_declared_package_and_metadata(
    built_artifacts: BuiltArtifacts,
) -> None:
    files = _wheel_files(built_artifacts.wheel)
    metadata_members = [
        member for member in files if member.endswith(".dist-info/METADATA")
    ]
    assert len(metadata_members) == 1, (
        f"{built_artifacts.wheel.name}: METADATA members {metadata_members!r}"
    )
    dist_info = metadata_members[0].removesuffix("/METADATA")
    metadata_files = {
        f"{dist_info}/METADATA",
        f"{dist_info}/WHEEL",
        f"{dist_info}/entry_points.txt",
        f"{dist_info}/licenses/LICENSE",
        f"{dist_info}/RECORD",
    }
    expected = (
        set(DECLARED_PACKAGE_MEMBERS | DECLARED_RESOURCE_MEMBERS) | metadata_files
    )
    assert set(files) == expected, _diff_message(
        built_artifacts.wheel.name, set(files), expected
    )

    metadata = Parser().parsestr(files[f"{dist_info}/METADATA"].decode("utf-8"))
    assert metadata.get("Name") == "ovcaq", (
        f"{built_artifacts.wheel.name}:{dist_info}/METADATA has Name "
        f"{metadata.get('Name')!r}"
    )
    assert metadata.get("Version") == built_artifacts.version, (
        f"{built_artifacts.wheel.name}:{dist_info}/METADATA has Version "
        f"{metadata.get('Version')!r}"
    )
    try:
        parsed_version = Version(built_artifacts.version)
    except InvalidVersion as error:
        raise AssertionError(
            f"{built_artifacts.wheel.name}:{dist_info}/METADATA has invalid "
            f"PEP 440 Version {built_artifacts.version!r}"
        ) from error
    assert parsed_version.is_devrelease, (
        f"{built_artifacts.wheel.name}:{dist_info}/METADATA Version is not a "
        f"PEP 440 development version: {built_artifacts.version!r}"
    )
    assert metadata.get("License-Expression") == "MIT", (
        f"{built_artifacts.wheel.name}:{dist_info}/METADATA has License-Expression "
        f"{metadata.get('License-Expression')!r}"
    )
    assert metadata.get("Requires-Python") == ">=3.12", (
        f"{built_artifacts.wheel.name}:{dist_info}/METADATA has Requires-Python "
        f"{metadata.get('Requires-Python')!r}"
    )
    assert sorted(metadata.get_all("Requires-Dist", [])) == ["rich", "textual"], (
        f"{built_artifacts.wheel.name}:{dist_info}/METADATA has Requires-Dist "
        f"{metadata.get_all('Requires-Dist', [])!r}"
    )
    entry_points = files[f"{dist_info}/entry_points.txt"].decode("utf-8")
    entry_point_config = ConfigParser(interpolation=None)
    entry_point_config.read_string(entry_points)
    assert entry_point_config.sections() == ["console_scripts"], (
        f"{built_artifacts.wheel.name}:{dist_info}/entry_points.txt has sections "
        f"{entry_point_config.sections()!r}"
    )
    assert dict(entry_point_config.items("console_scripts")) == {
        "ovcaq": "ovcaq.cli:main"
    }, f"{built_artifacts.wheel.name}:{dist_info}/entry_points.txt: {entry_points!r}"
    license_text = files[f"{dist_info}/licenses/LICENSE"].decode("utf-8")
    assert "MIT License" in license_text, (
        f"{built_artifacts.wheel.name}:{dist_info}/licenses/LICENSE is not MIT"
    )

    record = csv.reader(io.StringIO(files[f"{dist_info}/RECORD"].decode("utf-8")))
    recorded_members = {row[0] for row in record}
    assert recorded_members == expected, _diff_message(
        f"{built_artifacts.wheel.name}:{dist_info}/RECORD",
        recorded_members,
        expected,
    )


def test_wheel_members_are_unique_regular_files(
    built_artifacts: BuiltArtifacts,
) -> None:
    with zipfile.ZipFile(built_artifacts.wheel) as archive:
        members = archive.infolist()

    counts = Counter(member.filename for member in members)
    duplicates = sorted(name for name, count in counts.items() if count != 1)
    assert not duplicates, (
        f"{built_artifacts.wheel.name}: duplicate members: {duplicates!r}"
    )

    unsupported = []
    for member in members:
        unix_mode = member.external_attr >> 16
        file_type = stat.S_IFMT(unix_mode)
        if member.is_dir() or file_type not in {0, stat.S_IFREG}:
            unsupported.append(f"{member.filename} (mode={unix_mode:#o})")
    assert not unsupported, (
        f"{built_artifacts.wheel.name}: non-regular members: {unsupported!r}"
    )


def test_wheel_record_hashes_and_sizes_are_valid(
    built_artifacts: BuiltArtifacts,
) -> None:
    files = _wheel_files(built_artifacts.wheel)
    record_members = [name for name in files if name.endswith(".dist-info/RECORD")]
    assert len(record_members) == 1, (
        f"{built_artifacts.wheel.name}: RECORD members {record_members!r}"
    )
    record_member = record_members[0]
    rows = list(csv.reader(io.StringIO(files[record_member].decode("utf-8"))))
    assert all(len(row) == 3 for row in rows), (
        f"{built_artifacts.wheel.name}:{record_member}: malformed rows {rows!r}"
    )
    recorded_counts = Counter(row[0] for row in rows)
    duplicate_rows = sorted(
        member for member, count in recorded_counts.items() if count != 1
    )
    assert not duplicate_rows, (
        f"{built_artifacts.wheel.name}:{record_member}: duplicate rows "
        f"{duplicate_rows!r}"
    )

    for member, digest, size in rows:
        assert member in files, (
            f"{built_artifacts.wheel.name}:{record_member}: unknown {member!r}"
        )
        if member == record_member:
            assert digest == "" and size == "", (
                f"{built_artifacts.wheel.name}:{record_member}: RECORD must have "
                "empty hash and size"
            )
            continue

        expected_digest = (
            base64.urlsafe_b64encode(hashlib.sha256(files[member]).digest())
            .rstrip(b"=")
            .decode("ascii")
        )
        assert digest == f"sha256={expected_digest}", (
            f"{built_artifacts.wheel.name}:{record_member}: invalid digest for "
            f"{member!r}"
        )
        assert size == str(len(files[member])), (
            f"{built_artifacts.wheel.name}:{record_member}: invalid size for {member!r}"
        )


def test_sdist_contains_only_allowlisted_committed_inputs(
    built_artifacts: BuiltArtifacts,
) -> None:
    files = _sdist_files(built_artifacts.sdist)
    expected = (
        set(ROOT_METADATA)
        | {"PKG-INFO"}
        | {f"src/{member}" for member in DECLARED_PACKAGE_MEMBERS}
        | {f"src/{member}" for member in DECLARED_RESOURCE_MEMBERS}
        | _committed_evidence()
    )
    assert set(files) == expected, _diff_message(
        built_artifacts.sdist.name, set(files), expected
    )


def test_sdist_rebuilds_identical_wheel_offline(
    built_artifacts: BuiltArtifacts,
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "dist"
    output_dir.mkdir()
    uv = shutil.which("uv")
    assert uv is not None, "sdist build command unavailable: uv"
    run_checked(
        [
            uv,
            "--no-config",
            "build",
            "--offline",
            "--no-build-isolation",
            "--no-cache",
            "--no-progress",
            "--python",
            sys.executable,
            "--wheel",
            "--out-dir",
            output_dir,
            built_artifacts.sdist,
        ],
        cwd=tmp_path,
        env=isolated_environment(tmp_path / "sandbox"),
    )
    rebuilt_wheels = tuple(output_dir.glob("*.whl"))
    assert len(rebuilt_wheels) == 1, (
        f"{built_artifacts.sdist.name}: unexpected rebuilt wheels {rebuilt_wheels!r}"
    )
    rebuilt_files = _wheel_files(rebuilt_wheels[0])
    direct_files = _wheel_files(built_artifacts.wheel)
    assert rebuilt_files == direct_files, (
        f"{built_artifacts.sdist.name}: rebuilt wheel differs from direct wheel"
    )


def test_artifact_member_paths_exclude_private_and_generated_content(
    built_artifacts: BuiltArtifacts,
) -> None:
    violations = []
    for artifact_name, files in _artifact_file_sets(built_artifacts):
        for member in files:
            if reason := _path_violation(member):
                violations.append(f"{artifact_name}:{member}: {reason}")
    assert not violations, "forbidden artifact members:\n" + "\n".join(violations)


def test_artifact_text_excludes_personal_paths_and_likely_secrets(
    built_artifacts: BuiltArtifacts,
) -> None:
    violations = []
    patterns = (*PERSONAL_PATH_PATTERNS, *SECRET_PATTERNS)
    for artifact_name, files in _artifact_file_sets(built_artifacts):
        for member, text in _text_members(files):
            for pattern in patterns:
                if match := pattern.search(text):
                    violations.append(
                        f"{artifact_name}:{member}: matched {pattern.pattern!r} "
                        f"at byte/character {match.start()}"
                    )
    assert not violations, "sensitive artifact text:\n" + "\n".join(violations)


def test_production_sources_have_no_checkout_bootstrap() -> None:
    forbidden_patterns = (
        re.compile(r"\bsys\s*\.\s*path\s*\.\s*(?:insert|append)\s*\("),
        re.compile(r"\bsite\s*\.\s*addsitedir\s*\("),
        re.compile(r"\bPYTHONPATH\b"),
        re.compile(r"\b__package__\s*="),
        re.compile(
            r"Path\s*\(\s*__file__\s*\).*?\.parents?\s*(?:\[.*?\])?"
            r".*?[/'\"]src[/'\"]",
            re.DOTALL,
        ),
    )
    violations = []
    for member in sorted(DECLARED_PACKAGE_MEMBERS):
        source = PROJECT_ROOT / "src" / member
        text = source.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            if match := pattern.search(text):
                line = text.count("\n", 0, match.start()) + 1
                violations.append(f"src/{member}:{line}: {pattern.pattern}")
    assert not violations, "checkout-relative production bootstrap:\n" + "\n".join(
        violations
    )
