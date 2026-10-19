from __future__ import annotations

import json
import os
import re
import stat
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from ovcaq.paths import RuntimePaths, resolve_runtime_paths
from ovcaq.runtime.session import (
    EmergencyStateFailure,
    FailureDisposition,
    acknowledge_emergency_failure,
    record_state_failure,
    require_no_emergency_failure,
)
from ovcaq.state.schema import MAX_STATE_BYTES, MAX_STRING_BYTES

UTC_TIMESTAMP = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)"


def _reject(expected: type[BaseException], operation: Callable[[], object]) -> None:
    with pytest.raises(expected):
        operation()


def _decode(path: Path) -> dict[str, object]:
    def unique_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            assert key not in result, f"duplicate owned JSON key: {key}"
            result[key] = value
        return result

    payload = path.read_bytes()
    assert len(payload) <= MAX_STATE_BYTES
    document = json.loads(payload, object_pairs_hook=unique_keys)
    assert isinstance(document, dict)
    return document


def _state_notice_unavailable(site: str, detail: str) -> None:
    raise OSError("state storage unavailable")


def test_recorded_state_failure_blocks_caller_without_creating_emergency_gate(
    tmp_path: Path,
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    notice = tmp_path / "notice.json"

    def write_notice(site: str, detail: str) -> None:
        assert not (paths.runtime_root / "state-write-failed.json").exists()
        notice.write_text(json.dumps([site, detail]))

    disposition = record_state_failure(
        paths,
        site="transition.complete",
        detail="State commit was rejected.",
        write_state_notice=write_notice,
    )
    assert disposition == FailureDisposition(True, None, True)
    assert json.loads(notice.read_text()) == [
        "transition.complete",
        "State commit was rejected.",
    ]
    assert not (paths.runtime_root / "state-write-failed.json").exists()
    assert require_no_emergency_failure(resolve_runtime_paths(tmp_path)) is None
    with pytest.raises(FrozenInstanceError):
        disposition.block_launch = False


def test_failed_state_notice_publishes_private_synced_marker_and_persistent_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    paths, secret = resolve_runtime_paths(tmp_path), "private-environment-value-43d923"
    marker = paths.runtime_root / "state-write-failed.json"
    monkeypatch.setenv("OVCAQ_TEST_PRIVATE_VALUE", secret)
    site, detail = "session.finish", "Unable to commit completion."
    synced, real_fsync = [], os.fsync

    def observe_fsync(descriptor: int) -> None:
        information = os.fstat(descriptor)
        real_fsync(descriptor)
        if not (is_directory := stat.S_ISDIR(information.st_mode)):
            assert not marker.exists(), "marker became visible before file sync"
        synced.append((information.st_dev, information.st_ino, is_directory))

    def failed_notice(site: str, detail: str) -> None:
        assert not marker.exists()
        raise OSError(secret)

    monkeypatch.setattr(os, "fsync", observe_fsync)
    started, previous_umask = datetime.now(UTC), os.umask(0)
    try:
        assert record_state_failure(
            paths, site=site, detail=detail, write_state_notice=failed_notice
        ) == FailureDisposition(False, marker, True)
    finally:
        os.umask(previous_umask)
    finished = datetime.now(UTC)
    document = _decode(marker)
    version, created_at = document.pop("schema_version"), document.pop("created_at")
    assert type(version) is int and version == 1
    assert document == {"site": site, "detail": detail}
    assert isinstance(created_at, str) and re.fullmatch(UTC_TIMESTAMP, created_at)
    created = datetime.fromisoformat(created_at)
    assert created.utcoffset() == UTC.utcoffset(created)
    assert started.replace(microsecond=0) <= created <= finished
    information, parent = marker.stat(), paths.runtime_root.stat()
    file_sync = (information.st_dev, information.st_ino, False)
    assert (stat.S_IMODE(information.st_mode), file_sync in synced) == (0o600, True)
    parent_sync = (parent.st_dev, parent.st_ino, True)
    later_syncs = synced[synced.index(file_sync) + 1 :]
    assert stat.S_IMODE(parent.st_mode) == 0o700 and parent_sync in later_syncs
    before = marker.read_bytes()
    for _ in range(2):
        with pytest.raises(EmergencyStateFailure) as raised:
            require_no_emergency_failure(resolve_runtime_paths(tmp_path))
        assert secret not in str(raised.value)
    assert marker.read_bytes() == before and secret not in before.decode() + caplog.text


@pytest.mark.parametrize("field", ["site", "detail"])
@pytest.mark.parametrize(
    "value", ["", pytest.param("é" * (MAX_STRING_BYTES // 2), id="utf8-limit")]
)
def test_emergency_marker_preserves_empty_and_maximum_utf8_diagnostics(
    tmp_path: Path, field: str, value: str
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    diagnostics = {"site": "commit", "detail": "failed", field: value}
    disposition = record_state_failure(
        paths, **diagnostics, write_state_notice=_state_notice_unavailable
    )
    assert disposition.emergency_path is not None
    document = _decode(disposition.emergency_path)
    assert document["site"] == diagnostics["site"]
    assert document["detail"] == diagnostics["detail"]
    with pytest.raises(EmergencyStateFailure):
        require_no_emergency_failure(paths)


@pytest.mark.parametrize("field", ["site", "detail"])
@pytest.mark.parametrize(
    "value,expected",
    [
        (None, TypeError),
        (1, TypeError),
        pytest.param(
            "é" * (MAX_STRING_BYTES // 2 + 1),
            ValueError,
            id="utf8-over-limit",
        ),
    ],
)
def test_invalid_failure_diagnostics_are_rejected_without_publishing_marker(
    tmp_path: Path,
    field: str,
    value: object,
    expected: type[BaseException],
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    diagnostics = {"site": "commit", "detail": "failed", field: value}
    _reject(
        expected,
        lambda: record_state_failure(
            paths, **diagnostics, write_state_notice=_state_notice_unavailable
        ),
    )
    assert not (paths.runtime_root / "state-write-failed.json").exists()


def test_acknowledgement_requires_valid_state_and_durably_archives_exact_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    disposition = record_state_failure(
        paths,
        site="session.finish",
        detail="Could not record session.",
        write_state_notice=_state_notice_unavailable,
    )
    marker = disposition.emergency_path
    assert marker is not None
    evidence = marker.read_bytes()
    recorded = record_state_failure(
        paths,
        site="retry",
        detail="state writes work again",
        write_state_notice=lambda site, detail: None,
    )
    assert recorded == FailureDisposition(True, None, True)
    assert marker.read_bytes() == evidence
    _reject(ValueError, lambda: acknowledge_emergency_failure(paths, state_valid=False))
    assert marker.read_bytes() == evidence
    with pytest.raises(EmergencyStateFailure):
        require_no_emergency_failure(paths)
    synced: list[tuple[int, int]] = []
    real_fsync = os.fsync

    def observe_fsync(descriptor: int) -> None:
        information = os.fstat(descriptor)
        real_fsync(descriptor)
        synced.append((information.st_dev, information.st_ino))

    monkeypatch.setattr(os, "fsync", observe_fsync)
    archive = acknowledge_emergency_failure(paths, state_valid=True)
    assert archive.parent == paths.runtime_root / "reports"
    assert archive.name.startswith("emergency-") and archive.suffix == ".json"
    assert archive.name.removeprefix("emergency-").removesuffix(".json")
    assert archive.read_bytes() == evidence
    assert list(archive.parent.glob("emergency-*.json")) == [archive]
    assert stat.S_IMODE(archive.stat().st_mode) == 0o600
    assert stat.S_IMODE(archive.parent.stat().st_mode) == 0o700
    for directory in (paths.runtime_root, archive.parent):
        information = directory.stat()
        assert (information.st_dev, information.st_ino) in synced
    assert not marker.exists()
    assert require_no_emergency_failure(resolve_runtime_paths(tmp_path)) is None


def test_failed_archive_sync_keeps_emergency_evidence_and_launch_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    disposition = record_state_failure(
        paths,
        site="commit",
        detail="state failed",
        write_state_notice=_state_notice_unavailable,
    )
    marker = disposition.emergency_path
    assert marker is not None
    evidence = marker.read_bytes()
    reports = paths.runtime_root / "reports"
    reports.mkdir(mode=0o700, exist_ok=True)
    directory = reports.stat()
    real_fsync = os.fsync

    def deny_archive_sync(descriptor: int) -> None:
        if os.path.samestat(os.fstat(descriptor), directory):
            raise OSError("archive durability unavailable")
        real_fsync(descriptor)

    with monkeypatch.context() as patch:
        patch.setattr(os, "fsync", deny_archive_sync)
        _reject(OSError, lambda: acknowledge_emergency_failure(paths, state_valid=True))
    assert marker.read_bytes() == evidence
    with pytest.raises(EmergencyStateFailure):
        require_no_emergency_failure(resolve_runtime_paths(tmp_path))


@pytest.mark.parametrize(
    "damage",
    [
        "empty",
        "null",
        "malformed",
        "utf8",
        "deep",
        "duplicate",
        "oversized",
        "future",
        "bool-version",
        "extra",
        "time",
    ],
)
def test_invalid_emergency_evidence_blocks_launch_and_cannot_be_acknowledged(
    tmp_path: Path, damage: str
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    disposition = record_state_failure(
        paths,
        site="commit",
        detail="failed",
        write_state_notice=_state_notice_unavailable,
    )
    marker = disposition.emergency_path
    assert marker is not None
    document = _decode(marker)
    if damage == "empty":
        payload = b""
    elif damage == "null":
        payload = b"null"
    elif damage == "malformed":
        payload = b'{"schema_version":'
    elif damage == "utf8":
        payload = b"\xff"
    elif damage == "deep":
        payload = b"[" * 2000 + b"0" + b"]" * 2000
    elif damage == "duplicate":
        payload = (json.dumps(document)[:-1] + ', "schema_version": 1}').encode()
    elif damage == "oversized":
        payload = json.dumps(document).encode().ljust(MAX_STATE_BYTES + 1, b" ")
    else:
        key, value = {
            "future": ("schema_version", 2),
            "bool-version": ("schema_version", True),
            "extra": ("unknown", "value"),
            "time": ("created_at", "2026-09-14T10:00:00"),
        }[damage]
        payload = json.dumps(document | {key: value}).encode()
    marker.write_bytes(payload)
    with pytest.raises(EmergencyStateFailure):
        require_no_emergency_failure(paths)
    _reject(ValueError, lambda: acknowledge_emergency_failure(paths, state_valid=True))
    assert marker.read_bytes() == payload
    with pytest.raises(EmergencyStateFailure):
        require_no_emergency_failure(resolve_runtime_paths(tmp_path))


def test_emergency_evidence_at_byte_limit_can_be_acknowledged(tmp_path: Path) -> None:
    paths = resolve_runtime_paths(tmp_path)
    disposition = record_state_failure(
        paths,
        site="commit",
        detail="failed",
        write_state_notice=_state_notice_unavailable,
    )
    marker = disposition.emergency_path
    assert marker is not None
    evidence = marker.read_bytes().ljust(MAX_STATE_BYTES, b" ")
    marker.write_bytes(evidence)
    with pytest.raises(EmergencyStateFailure):
        require_no_emergency_failure(paths)
    archive = acknowledge_emergency_failure(paths, state_valid=True)
    assert archive.read_bytes() == evidence
    assert not marker.exists()


def _first_failure_marker(paths: RuntimePaths) -> Path:
    disposition = record_state_failure(
        paths,
        site="commit",
        detail="first failure",
        write_state_notice=_state_notice_unavailable,
    )
    marker = disposition.emergency_path
    assert marker is not None
    return marker


def _finalization_hooks(
    marker: Path, reports: Path, boundary: str, change_evidence: Callable[[], None]
) -> tuple[Callable[[int], None], Callable[..., Any]]:
    real_fsync = os.fsync
    retired = False

    def synchronize(descriptor: int) -> None:
        is_archive_sync = (
            reports.exists()
            and os.path.samestat(os.fstat(descriptor), reports.stat())
            and any(reports.glob("emergency-*.json"))
        )
        is_final_runtime_sync = retired and os.path.samestat(
            os.fstat(descriptor), marker.parent.stat()
        )
        if is_archive_sync and boundary == "before-archive-sync":
            change_evidence()
        if is_final_runtime_sync and boundary == "before-runtime-sync":
            change_evidence()
        real_fsync(descriptor)
        if is_archive_sync and boundary == "after-archive-sync":
            change_evidence()
        if is_final_runtime_sync and boundary == "after-runtime-sync":
            change_evidence()

    def intercept_retirement(operation: Callable[..., Any]) -> Callable[..., Any]:
        def retire(source: Any, *args: Any, **kwargs: Any) -> Any:
            nonlocal retired
            removes_marker = Path(os.fsdecode(source)).name == marker.name
            if boundary == "retirement" and removes_marker:
                change_evidence()
            result = operation(source, *args, **kwargs)
            if removes_marker:
                retired = True
                if boundary == "after-retirement":
                    change_evidence()
            return result

        return retire

    return synchronize, intercept_retirement


@pytest.mark.parametrize("change", ["replacement", "rewrite"])
@pytest.mark.parametrize(
    "boundary",
    [
        "before-archive-sync",
        "after-archive-sync",
        "retirement",
        "after-retirement",
        "before-runtime-sync",
        "after-runtime-sync",
    ],
)
def test_acknowledgement_preserves_new_evidence_at_finalization_boundaries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str, boundary: str
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    marker = _first_failure_marker(paths)
    evidence = json.dumps(_decode(marker) | {"detail": "later failure"}).encode()
    reports = paths.runtime_root / "reports"
    replacement = tmp_path / "replacement.json"
    replacement.write_bytes(evidence)
    replacement.chmod(0o600)
    real_replace, real_fsync = os.replace, os.fsync
    changed = False

    def change_evidence() -> None:
        nonlocal changed
        if changed:
            return
        changed = True
        if change == "replacement":
            real_replace(replacement, marker)
        else:
            # A writer that already has the evidence open can rewrite its inode
            # even after acknowledgement has moved it into the archive.
            os.lseek(writer, 0, os.SEEK_SET)
            os.write(writer, evidence)
            os.ftruncate(writer, len(evidence))
            real_fsync(writer)

    synchronize, intercept_retirement = _finalization_hooks(
        marker, reports, boundary, change_evidence
    )
    writer = os.open(marker, os.O_WRONLY)
    try:
        with monkeypatch.context() as patch:
            patch.setattr(os, "fsync", synchronize)
            for name in ("unlink", "remove", "rename", "replace"):
                patch.setattr(os, name, intercept_retirement(getattr(os, name)))
            with pytest.raises(ValueError):
                acknowledge_emergency_failure(paths, state_valid=True)
    finally:
        os.close(writer)

    assert changed, "finalization race was not exercised"
    retained = [path for path in reports.glob("emergency-*.json") if path.is_file()]
    if marker.exists():
        retained.append(marker)
        with pytest.raises(EmergencyStateFailure):
            require_no_emergency_failure(resolve_runtime_paths(tmp_path))
    assert any(path.read_bytes() == evidence for path in retained)


def _is_archive_destination(
    destination: Any, directory: int | None, reports: Path
) -> bool:
    path = Path(os.fsdecode(destination))
    if not (path.name.startswith("emergency-") and path.suffix == ".json"):
        return False
    if path.is_absolute():
        return path.parent == reports
    if directory is not None:
        return os.path.samestat(os.fstat(directory), reports.stat())
    return path.parent.absolute() == reports


def _acknowledgement_failure_hooks(
    marker: Path, reports: Path, failure: str, inject_failure: Callable[[], None]
) -> tuple[Callable[..., Any], Callable[..., int], Callable[[int], None]]:
    real_fsync, real_open = os.fsync, os.open

    def publish(operation: Callable[..., Any]) -> Callable[..., Any]:
        def interrupted(
            source: Any, destination: Any, *args: Any, **kwargs: Any
        ) -> Any:
            if failure == "archive-publication" and _is_archive_destination(
                destination, kwargs.get("dst_dir_fd"), reports
            ):
                inject_failure()
            return operation(source, destination, *args, **kwargs)

        return interrupted

    def open_archive(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        if (
            failure == "archive-publication"
            and flags & os.O_CREAT
            and _is_archive_destination(path, kwargs.get("dir_fd"), reports)
        ):
            inject_failure()
        return real_open(path, flags, *args, **kwargs)

    def synchronize(descriptor: int) -> None:
        if (
            failure == "runtime-sync-after-retirement"
            and not marker.exists()
            and os.path.samestat(os.fstat(descriptor), marker.parent.stat())
            and any(reports.glob("emergency-*.json"))
        ):
            inject_failure()
        real_fsync(descriptor)

    return publish, open_archive, synchronize


@pytest.mark.parametrize("replacement_arrives", [False, True])
@pytest.mark.parametrize(
    "failure", ["archive-publication", "runtime-sync-after-retirement"]
)
def test_failed_acknowledgement_preserves_or_restores_canonical_blocking_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
    replacement_arrives: bool,
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    marker = _first_failure_marker(paths)
    original = marker.read_bytes()
    replacement = tmp_path / "replacement.json"
    replacement.write_bytes(
        json.dumps(_decode(marker) | {"detail": "later failure"}).encode()
    )
    replacement.chmod(0o600)
    expected = replacement.read_bytes() if replacement_arrives else original
    reports = paths.runtime_root / "reports"
    real_replace = os.replace
    failed = False

    def inject_failure() -> None:
        nonlocal failed
        if failed:
            return
        failed = True
        if replacement_arrives:
            real_replace(replacement, marker)
        raise OSError("injected emergency archive failure")

    publish, open_archive, synchronize = _acknowledgement_failure_hooks(
        marker, reports, failure, inject_failure
    )
    with monkeypatch.context() as patch:
        patch.setattr(os, "open", open_archive)
        patch.setattr(os, "fsync", synchronize)
        for name in ("link", "rename", "replace"):
            patch.setattr(os, name, publish(getattr(os, name)))
        _reject(OSError, lambda: acknowledge_emergency_failure(paths, state_valid=True))

    assert failed, "acknowledgement failure boundary was not exercised"
    assert marker.read_bytes() == expected
    with pytest.raises(EmergencyStateFailure):
        require_no_emergency_failure(resolve_runtime_paths(tmp_path))
    if failure == "runtime-sync-after-retirement":
        preserved = [marker, *reports.glob("emergency-*.json")]
        assert any(path.read_bytes() == original for path in preserved)


@pytest.mark.parametrize(
    "obstacle", ["symlink", "dangling", "directory", "fifo", "mode"]
)
def test_unsafe_emergency_marker_fails_closed_without_changing_evidence(
    tmp_path: Path, obstacle: str
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    paths.runtime_root.mkdir(mode=0o700, parents=True)
    marker = paths.runtime_root / "state-write-failed.json"
    sentinel = tmp_path / "sentinel"
    sentinel.write_bytes(b"preserve outside evidence")
    if obstacle == "symlink":
        marker.symlink_to(sentinel)
    elif obstacle == "dangling":
        marker.symlink_to(tmp_path / "absent")
    elif obstacle == "directory":
        marker.mkdir(mode=0o700)
    elif obstacle == "fifo":
        os.mkfifo(marker, mode=0o600)
    else:
        record_state_failure(
            paths,
            site="commit",
            detail="failed",
            write_state_notice=_state_notice_unavailable,
        )
        marker.chmod(0o666)
    before = marker.lstat()
    with pytest.raises(EmergencyStateFailure):
        require_no_emergency_failure(paths)
    _reject(ValueError, lambda: acknowledge_emergency_failure(paths, state_valid=True))
    _reject(
        ValueError,
        lambda: record_state_failure(
            paths,
            site="another-commit",
            detail="another failure",
            write_state_notice=_state_notice_unavailable,
        ),
    )
    after = marker.lstat()
    assert (after.st_ino, after.st_mode) == (before.st_ino, before.st_mode)
    assert sentinel.read_bytes() == b"preserve outside evidence"
    assert not (tmp_path / "absent").exists()


@pytest.mark.parametrize("obstacle", ["symlink", "mode"])
def test_unsafe_report_directory_refuses_acknowledgement_and_preserves_gate(
    tmp_path: Path, obstacle: str
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    disposition = record_state_failure(
        paths,
        site="commit",
        detail="failed",
        write_state_notice=_state_notice_unavailable,
    )
    marker = disposition.emergency_path
    assert marker is not None
    evidence = marker.read_bytes()
    reports = paths.runtime_root / "reports"
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    if obstacle == "symlink":
        reports.symlink_to(outside, target_is_directory=True)
    else:
        reports.mkdir(mode=0o700, exist_ok=True)
        reports.chmod(0o777)
    _reject(ValueError, lambda: acknowledge_emergency_failure(paths, state_valid=True))
    assert marker.read_bytes() == evidence
    assert list(outside.iterdir()) == []
    with pytest.raises(EmergencyStateFailure):
        require_no_emergency_failure(paths)


def test_marker_replacement_during_acknowledgement_preserves_new_failure_and_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    disposition = record_state_failure(
        paths,
        site="commit",
        detail="first failure",
        write_state_notice=_state_notice_unavailable,
    )
    marker = disposition.emergency_path
    assert marker is not None
    original = marker.stat()
    replacement = tmp_path / "replacement.json"
    replacement.write_text(json.dumps(_decode(marker) | {"detail": "later failure"}))
    replacement.chmod(0o600)
    new_evidence = replacement.read_bytes()
    real_fstat = os.fstat
    replaced = False

    def replace_open_marker(descriptor: int) -> os.stat_result:
        nonlocal replaced
        information = real_fstat(descriptor)
        if not replaced and os.path.samestat(information, original):
            os.replace(replacement, marker)
            replaced = True
        return information

    with monkeypatch.context() as patch:
        patch.setattr(os, "fstat", replace_open_marker)
        _reject(
            ValueError, lambda: acknowledge_emergency_failure(paths, state_valid=True)
        )
    assert replaced, "replacement race was not exercised"
    assert marker.read_bytes() == new_evidence
    with pytest.raises(EmergencyStateFailure):
        require_no_emergency_failure(resolve_runtime_paths(tmp_path))
