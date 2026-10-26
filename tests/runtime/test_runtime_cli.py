from __future__ import annotations

import builtins
import errno
import fcntl
import io
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from ovcaq.cli import build_parser, command_inventory, main, render_command_reference
from ovcaq.config import runtime_settings
from ovcaq.errors import ErrorCode
from ovcaq.paths import ensure_runtime_layout, resolve_runtime_paths
from ovcaq.runtime.capability import CapabilityResult, probe_platform
from ovcaq.runtime.registry import FleetEntry, FleetRegistry, RunLock, process_identity
from ovcaq.runtime.session import (
    SessionMetadata,
    create_session,
    publish_run_metadata,
    record_state_failure,
)
from ovcaq.state.schema import MAX_STATE_BYTES


def _invoke(
    root: Path,
    capsys: pytest.CaptureFixture[str],
    *arguments: str,
    json_mode: bool = True,
) -> tuple[int, str, str]:
    argv = ["--root", str(root)]
    if json_mode:
        argv.append("--json")
    result = main([*argv, *arguments])
    captured = capsys.readouterr()
    return result, captured.out, captured.err


def _success(result: tuple[int, str, str]) -> dict[str, Any]:
    code, stdout, stderr = result
    assert code == 0, stderr
    assert stderr == ""
    return json.loads(stdout)


def _failure(result: tuple[int, str, str], error_code: str) -> dict[str, Any]:
    code, stdout, stderr = result
    assert code == 1
    assert stdout == ""
    assert "Traceback" not in stderr
    payload = json.loads(stderr)
    assert set(payload) == {"ok", "error"}
    assert payload["ok"] is False
    assert set(payload["error"]) == {"code", "message", "path"}
    assert payload["error"]["code"] == error_code
    assert isinstance(payload["error"]["message"], str)
    assert payload["error"]["message"]
    return payload


def _initialize(root: Path, capsys: pytest.CaptureFixture[str]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    _success(_invoke(root, capsys, "init"))
    return root / "docs/dev/project-management/ovcaq"


def test_live_parser_inventory_and_generated_operations_include_runtime_commands() -> (
    None
):
    parser = build_parser()
    for arguments in (
        ["status"],
        ["doctor"],
        ["doctor", "--acknowledge-emergency"],
        ["logs"],
        ["logs", "--session", "session-1", "--kind", "normalized", "--follow"],
        ["logs", "purge", "--session", "session-1"],
        ["logs", "purge", "--before", "2026-01-01T00:00:00Z", "--apply"],
    ):
        parser.parse_args(["--root", "/tmp/runtime-cli-project", *arguments])

    inventory = command_inventory(parser)
    assert any(" status" in usage for usage in inventory)
    assert any(
        " doctor" in usage and "--acknowledge-emergency" in usage for usage in inventory
    )
    assert any(" logs" in usage and "--follow" in usage for usage in inventory)
    assert any(" logs purge" in usage and "--apply" in usage for usage in inventory)
    reference = Path(__file__).resolve().parents[2] / "docs/operations.md"
    rendered = render_command_reference(parser)
    assert reference.read_text(encoding="utf-8") == rendered
    documented = tuple(
        line for line in rendered.splitlines() if line.startswith("ovcaq ")
    )
    assert documented == inventory
    assert rendered.startswith("# Operations\n")
    prose = " ".join(rendered.split())
    assert "compare-and-set revisions fail closed." in prose
    assert "`stall` and `park` retain durable recovery intent" in prose
    assert "`defer` requires an `op_id` in its JSON record." in prose
    assert "relative paths resolve from the discovered project root." in prose
    assert (
        "Runtime roots remain inside the project and reject symlink components."
        in prose
    )
    assert "After a second consecutive park, the durable pause returns exit 4." in prose
    assert "Exact replay returns the same halt without another park." in prose


@pytest.mark.parametrize("state_status", ("available", "missing", "invalid"))
def test_status_reports_authoritative_state_health_without_crashing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], state_status: str
) -> None:
    root = tmp_path / "project"
    runtime = _initialize(root, capsys)
    state_path = runtime / "state.json"
    if state_status == "missing":
        state_path.unlink()
    elif state_status == "invalid":
        state_path.write_bytes(b"{malformed-state")

    payload = _success(_invoke(root, capsys, "status"))

    assert set(payload) == {
        "schema_version",
        "state",
        "run",
        "evidence",
        "purge_preview",
        "attention",
    }
    assert payload["schema_version"] == 1
    assert payload["state"] == state_status
    assert payload["run"] == "idle"
    assert payload["attention"] is None
    assert set(payload["evidence"]) == {
        "runtime_root",
        "sessions",
        "total_bytes",
        "max_retained_bytes",
        "min_free_bytes",
    }
    assert payload["evidence"]["runtime_root"] == str(runtime)
    assert payload["evidence"]["sessions"] == []
    assert payload["evidence"]["total_bytes"] == 0
    assert payload["purge_preview"]["selected"] == []
    assert payload["purge_preview"]["total_bytes"] == 0
    assert payload["purge_preview"]["applied"] is False


@pytest.mark.parametrize(
    "arguments",
    (
        ("logs", "--follow"),
        ("logs", "--kind", "unknown"),
        ("logs", "purge"),
        ("logs", "purge", "--session", "one", "--before", "2026-01-01T00:00:00Z"),
        ("logs", "purge", "--before", "not-a-timestamp"),
    ),
    ids=("json-follow", "unknown-kind", "no-selector", "two-selectors", "invalid-date"),
)
def test_invalid_runtime_command_arguments_have_stable_usage_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], arguments: tuple[str, ...]
) -> None:
    _initialize(tmp_path, capsys)
    _failure(_invoke(tmp_path, capsys, *arguments), "usage")


def test_missing_retained_session_has_stable_runtime_format_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _initialize(tmp_path, capsys)
    assert ErrorCode.RUNTIME_FORMAT.value == "runtime_format"
    _failure(_invoke(tmp_path, capsys, "logs", "--session", "absent"), "runtime_format")
    _failure(_invoke(tmp_path, capsys, "logs"), "runtime_format")


@pytest.mark.parametrize(
    "parent_arguments,json_mode",
    (
        (("--session", "other"), True),
        (("--kind", "raw"), True),
        (("--kind", "normalized"), True),
        (("--follow",), True),
        (("--follow",), False),
    ),
)
@pytest.mark.parametrize("apply", (False, True))
def test_purge_rejects_parent_log_options_without_removing_evidence(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    parent_arguments: tuple[str, ...],
    apply: bool,
    json_mode: bool,
) -> None:
    _initialize(tmp_path, capsys)
    _paths, _metadata, selected = _session(tmp_path, "selected")
    _paths, _metadata, other = _session(tmp_path, "other")
    retained = {
        path: path.read_bytes()
        for session in (selected, other)
        for path in session.root.iterdir()
        if path.is_file()
    }

    result = _invoke(
        tmp_path,
        capsys,
        "logs",
        *parent_arguments,
        "purge",
        "--session",
        "selected",
        *(("--apply",) if apply else ()),
        json_mode=json_mode,
    )
    if json_mode:
        _failure(result, "usage")
    else:
        assert result[0] == 1
        assert result[1] == ""
        assert result[2].strip()
        assert "Traceback" not in result[2]

    assert {path: path.read_bytes() for path in retained} == retained


def _session(
    root: Path, session_id: str, started_at: str = "2026-01-01T00:00:00Z"
) -> Any:
    paths = resolve_runtime_paths(root, xdg_state_home=root / "fleet")
    ensure_runtime_layout(paths)
    identity = process_identity(os.getpid())
    assert identity is not None
    metadata = SessionMetadata(
        schema_version=1,
        run_id="run-1",
        session_id=session_id,
        agent="command",
        pid=os.getpid(),
        process_start=identity.started,
        started_at=started_at,
    )
    session = create_session(paths, metadata)
    session.raw.write_bytes(b"retained raw output\n")
    session.normalized.write_bytes(b'{"type":"observation"}\n')
    return paths, metadata, session


@pytest.mark.parametrize(
    "locked", (False, True), ids=("metadata-only", "authoritative-lock")
)
def test_status_requires_matching_live_metadata_and_authoritative_lock_for_activity(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], locked: bool
) -> None:
    _initialize(tmp_path, capsys)
    paths, metadata, _session_paths = _session(tmp_path, "session-1")
    publish_run_metadata(paths, metadata)
    if locked:
        with RunLock.acquire(paths.run_lock):
            payload = _success(_invoke(tmp_path, capsys, "status"))
            assert payload["run"] == "active"
            log = _success(_invoke(tmp_path, capsys, "logs", "--session", "session-1"))
            assert log["active"] is True
    else:
        payload = _success(_invoke(tmp_path, capsys, "status"))
        assert payload["run"] == "inconsistent"


@pytest.mark.parametrize(
    "corruption",
    (
        "missing",
        "stale-process",
        "wrong-pid-type",
        "missing-field",
        "extra-field",
        "malformed",
        "future",
    ),
)
def test_held_run_lock_does_not_make_untrusted_run_metadata_active(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], corruption: str
) -> None:
    _initialize(tmp_path, capsys)
    paths, metadata, _session_paths = _session(tmp_path, "identity-checked-session")
    publish_run_metadata(paths, metadata)
    record = json.loads(paths.run_metadata.read_bytes())
    if corruption == "stale-process":
        record["process_start"] = "stale-process-start-token"
    elif corruption == "wrong-pid-type":
        record["pid"] = str(os.getpid())
    elif corruption == "missing-field":
        del record["run_id"]
    elif corruption == "extra-field":
        record["undeclared"] = True
    elif corruption == "future":
        record["schema_version"] = 999
    paths.run_metadata.write_text(
        "{invalid-json" if corruption == "malformed" else json.dumps(record),
        encoding="utf-8",
    )
    if corruption == "missing":
        paths.run_metadata.unlink()

    with RunLock.acquire(paths.run_lock):
        payload = _success(_invoke(tmp_path, capsys, "status"))
        report = _doctor_payload(tmp_path, capsys)

    assert payload["state"] == "available"
    assert payload["run"] == "inconsistent"
    assert report["ok"] is False
    reason = _doctor_checks(report)["run"]
    assert isinstance(reason, str) and reason.strip()
    assert reason not in {"available", "idle", "active", "inconsistent"}


def test_registry_only_runtime_is_inconsistent_with_an_operator_visible_reason(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "fleet"))
    _initialize(tmp_path, capsys)
    paths = resolve_runtime_paths(tmp_path)
    identity = process_identity(os.getpid())
    assert identity is not None
    FleetRegistry(paths.fleet_root).publish(
        FleetEntry(
            schema_version=1,
            root=tmp_path,
            pid=identity.pid,
            process_start=identity.started,
            run_id="registry-only-run",
            agent="command",
            started_at="2026-01-01T00:00:00Z",
        )
    )

    status = _success(_invoke(tmp_path, capsys, "status"))
    assert status["run"] == "inconsistent"
    assert status["evidence"]["sessions"] == []
    assert not paths.run_metadata.exists()
    report = _doctor_payload(tmp_path, capsys)
    assert report["ok"] is False
    reason = _doctor_checks(report)["run"]
    assert isinstance(reason, str) and reason.strip()
    assert reason not in {"available", "idle", "active", "inconsistent"}


def _launch_lock_owner(lock_path: Path) -> subprocess.CompletedProcess[str]:
    launcher = """
import sys
from pathlib import Path
from ovcaq.runtime.registry import RunLock
try:
    with RunLock.acquire(Path(sys.argv[1])):
        print("owned", flush=True)
except Exception as error:
    print(type(error).__name__, file=sys.stderr)
    sys.exit(1)
"""
    return subprocess.run(
        [sys.executable, "-c", launcher, str(lock_path)],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


@pytest.mark.parametrize("command", ("status", "doctor"))
def test_read_only_observation_cannot_make_a_real_launcher_a_duplicate(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    command: str,
) -> None:
    _initialize(tmp_path, capsys)
    paths, _metadata, _session_paths = _session(tmp_path, "retained")
    paths.run_lock.touch(mode=0o600, exist_ok=True)
    original_lock = paths.run_lock.stat()
    real_flock = fcntl.flock
    real_listdir, real_scandir = os.listdir, os.scandir
    attempts: list[subprocess.CompletedProcess[str]] = []

    def launch() -> None:
        attempts.append(_launch_lock_owner(paths.run_lock))

    def observe_lock(descriptor: Any, operation: int) -> None:
        real_flock(descriptor, operation)
        number = descriptor if isinstance(descriptor, int) else descriptor.fileno()
        if operation & (fcntl.LOCK_EX | fcntl.LOCK_SH) and os.path.samestat(
            original_lock, os.fstat(number)
        ):
            # Pause lock ownership at the OS boundary so a real
            # launcher runs during it, rather than relying on a timing race.
            launch()

    def observe_listdir(path: Any = ".") -> Any:
        if _same_directory(path, _session_paths.root.parent):
            launch()
        return real_listdir(path)

    def observe_scandir(path: Any = ".") -> Any:
        if _same_directory(path, _session_paths.root.parent):
            launch()
        return real_scandir(path)

    launch()
    with monkeypatch.context() as boundary:
        boundary.setattr(fcntl, "flock", observe_lock)
        boundary.setattr(os, "listdir", observe_listdir)
        boundary.setattr(os, "scandir", observe_scandir)
        payload = _success(_invoke(tmp_path, capsys, command))
    launch()

    assert all(attempt.returncode == 0 for attempt in attempts), [
        attempt.stderr for attempt in attempts if attempt.returncode
    ]
    assert all(attempt.stdout == "owned\n" for attempt in attempts)
    assert payload.get("run", "idle") == "idle"


@pytest.mark.parametrize("target", ("run", "session"))
@pytest.mark.parametrize(
    "field,value",
    (
        ("run_id", ""),
        ("run_id", "."),
        ("run_id", ".."),
        ("run_id", "../escaped"),
        ("run_id", "/escaped"),
        ("run_id", "nested/id"),
        ("run_id", "bad\x00id"),
        ("session_id", ""),
        ("session_id", "."),
        ("session_id", ".."),
        ("session_id", "../escaped"),
        ("session_id", "/escaped"),
        ("session_id", "nested/id"),
        ("session_id", "bad\x00id"),
        ("started_at", "2026-01-01T00:00:00+02:00"),
        ("started_at", "2026-01-01T00:00:00-02:00"),
        ("started_at", "2026-01-01T00:00:00"),
        ("agent", ""),
        ("process_start", ""),
    ),
)
def test_runtime_readers_reject_unsafe_ids_non_utc_times_and_empty_required_strings(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    target: str,
    field: str,
    value: str,
) -> None:
    _initialize(tmp_path, capsys)
    paths, metadata, session = _session(tmp_path, "session-1")
    publish_run_metadata(paths, metadata)
    destination = paths.run_metadata if target == "run" else session.metadata
    record = json.loads(destination.read_bytes())
    record[field] = value
    destination.write_text(json.dumps(record), encoding="utf-8")
    original = destination.read_bytes()

    with RunLock.acquire(paths.run_lock):
        if target == "run":
            payload = _success(_invoke(tmp_path, capsys, "status"))
            assert payload["state"] == "available"
            assert payload["run"] == "inconsistent"
        else:
            _failure(
                _invoke(tmp_path, capsys, "logs", "--session", "session-1"),
                "runtime_format",
            )

    assert destination.read_bytes() == original
    assert session.raw.read_bytes() == b"retained raw output\n"


@pytest.mark.parametrize("kind", ("raw", "normalized"))
def test_logs_locate_explicit_and_newest_evidence_without_streaming_contents(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], kind: str
) -> None:
    _initialize(tmp_path, capsys)
    _paths, _metadata, older = _session(tmp_path, "older", "2026-01-01T00:00:00Z")
    _paths, _metadata, newer = _session(tmp_path, "newer", "2026-02-01T00:00:00Z")
    # Filesystem timestamps must not override the declared session start time.
    os.utime(older.metadata, (2_000_000_000, 2_000_000_000))
    selected = getattr(newer, kind)
    default = _success(_invoke(tmp_path, capsys, "logs", "--kind", kind))
    assert default == {
        "schema_version": 1,
        "session_id": "newer",
        "kind": kind,
        "path": str(selected),
        "size_bytes": selected.stat().st_size,
        "active": False,
    }
    explicit = _success(_invoke(tmp_path, capsys, "logs", "--session", "older"))
    assert explicit["session_id"] == "older"
    assert explicit["kind"] == "raw"
    assert explicit["path"] == str(older.raw)
    code, stdout, stderr = _invoke(
        tmp_path, capsys, "logs", "--session", "older", json_mode=False
    )
    assert code == 0
    assert str(older.raw) in stdout
    assert "retained raw output" not in stdout
    assert stderr == ""


def test_default_log_selection_breaks_equal_start_times_deterministically(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _initialize(tmp_path, capsys)
    _session(tmp_path, "z-session")
    _session(tmp_path, "a-session")
    first = _success(_invoke(tmp_path, capsys, "logs"))
    second = _success(_invoke(tmp_path, capsys, "logs"))
    assert first == second
    assert first["session_id"] in {"a-session", "z-session"}
    reverse_root = tmp_path / "reversed-creation-order"
    _initialize(reverse_root, capsys)
    _session(reverse_root, "a-session")
    _session(reverse_root, "z-session")
    reversed_selection = _success(_invoke(reverse_root, capsys, "logs"))
    assert reversed_selection["session_id"] == first["session_id"]


@pytest.mark.parametrize(
    ("target", "corruption"),
    (
        ("metadata", "missing"),
        ("metadata", "symlink"),
        ("metadata", "directory"),
        ("metadata", "malformed"),
        ("metadata", "future"),
        ("raw", "missing"),
        ("raw", "symlink"),
        ("raw", "directory"),
    ),
)
def test_logs_reject_unsafe_or_invalid_evidence_without_following_links(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], corruption: str, target: str
) -> None:
    _initialize(tmp_path, capsys)
    _paths, _metadata, session = _session(tmp_path, "session-1")
    damaged = getattr(session, target)
    original = damaged.read_bytes()
    outside = tmp_path / "outside-evidence"
    outside.write_bytes(original)
    if corruption in {"missing", "symlink", "directory"}:
        damaged.unlink()
        if corruption == "symlink":
            damaged.symlink_to(outside)
        elif corruption == "directory":
            damaged.mkdir()
    elif corruption == "malformed":
        damaged.write_bytes(b"{broken")
    else:
        data = json.loads(original)
        data["schema_version"] = 999
        damaged.write_text(json.dumps(data), encoding="utf-8")
    _failure(
        _invoke(tmp_path, capsys, "logs", "--session", "session-1"), "runtime_format"
    )
    assert outside.read_bytes() == original
    status = _success(_invoke(tmp_path, capsys, "status"))
    assert set(status) == {
        "schema_version",
        "state",
        "run",
        "evidence",
        "purge_preview",
        "attention",
    }
    assert status["state"] == "available"
    assert status["run"] != "active"


def _assert_doctor_report(payload: dict[str, Any], runtime: Path) -> None:
    assert set(payload) == {
        "schema_version",
        "ok",
        "paths",
        "capabilities",
        "checks",
        "purge_preview",
        "attention",
        "acknowledged_emergency_archive",
    }
    assert payload["schema_version"] == 1
    assert payload["attention"] is None
    assert payload["acknowledged_emergency_archive"] is None
    assert isinstance(payload["ok"], bool)
    paths = payload["paths"]
    assert set(paths) == {
        "project_root",
        "runtime_root",
        "state_file",
        "run_lock",
        "run_metadata",
        "events",
        "metrics",
        "sessions",
        "reports",
        "fleet_root",
        "fleet_lock",
        "retention_lock",
    }
    assert all(
        isinstance(path, str) and Path(path).is_absolute() for path in paths.values()
    )
    assert paths["runtime_root"] == str(runtime)
    assert paths["state_file"] == str(runtime / "state.json")
    assert paths["sessions"] == str(runtime / "sessions")
    capabilities = json.dumps(payload["capabilities"])
    for result in probe_platform():
        assert result.name in capabilities
    for entries in (payload["capabilities"], payload["checks"]):
        names = [
            entry["name"]
            for entry in entries
            if isinstance(entry, dict) and "name" in entry
        ]
        assert names
        assert names == sorted(names)


def _doctor_payload(root: Path, capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    _code, stdout, stderr = _invoke(root, capsys, "doctor")
    assert stderr == ""
    payload = json.loads(stdout)
    _assert_doctor_report(payload, root / "docs/dev/project-management/ovcaq")
    return payload


def _doctor_checks(payload: dict[str, Any]) -> dict[str, str]:
    assert all(set(check) == {"name", "status"} for check in payload["checks"])
    checks = {check["name"]: check["status"] for check in payload["checks"]}
    assert len(checks) == len(payload["checks"])
    return checks


@pytest.mark.parametrize(
    "failure", (None, "permissions", "writability", "retained_budget", "free_space")
)
def test_doctor_reports_resource_facts_and_fails_for_each_blocking_resource(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], failure: str | None
) -> None:
    volume = os.statvfs(tmp_path)
    minimum_free = (
        volume.f_blocks * volume.f_frsize * 2 if failure == "free_space" else 1
    )
    maximum_retained = 1 if failure == "retained_budget" else 1024 * 1024
    (tmp_path / "ovcaq.toml").write_text(
        f"[runtime]\nmax_retained_bytes = {maximum_retained}\n"
        f"min_free_bytes = {minimum_free}\n",
        encoding="utf-8",
    )
    runtime = _initialize(tmp_path, capsys)
    _paths, _metadata, session = _session(tmp_path, "retained")
    original_mode = runtime.stat().st_mode & 0o777
    if failure == "permissions":
        runtime.chmod(0o755)
    elif failure == "writability":
        runtime.chmod(0o500)
    try:
        report = _doctor_payload(tmp_path, capsys)
        repeated = _doctor_payload(tmp_path, capsys)
    finally:
        runtime.chmod(original_mode)

    checks = _doctor_checks(report)
    assert set(checks) == {
        "evidence",
        "run",
        "state",
        "permissions",
        "writability",
        "retained_budget",
        "free_space",
    }
    assert checks == _doctor_checks(repeated)
    if failure is None:
        assert checks == dict.fromkeys(checks, "available")
        assert report["ok"] is True
    else:
        assert isinstance(checks[failure], str) and checks[failure].strip()
        assert checks[failure] != "available"
        assert report["ok"] is False
        assert checks["state"] == "available"
        assert checks["run"] == "available"
    assert session.raw.read_bytes() == b"retained raw output\n"


def _same_directory(candidate: Any, expected: Path) -> bool:
    try:
        info = os.fstat(candidate) if isinstance(candidate, int) else os.stat(candidate)
        return os.path.samestat(info, expected.stat())
    except (OSError, TypeError):
        return False


@pytest.mark.parametrize("command", ("status", "doctor"))
def test_inventory_io_failure_is_visible_in_the_public_report(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    command: str,
) -> None:
    _initialize(tmp_path, capsys)
    _paths, _metadata, session = _session(tmp_path, "retained")
    real_listdir, real_scandir = os.listdir, os.scandir

    def unavailable_listdir(path: Any = ".") -> Any:
        if _same_directory(path, session.root.parent):
            raise OSError(errno.EIO, "injected evidence inventory failure")
        return real_listdir(path)

    def unavailable_scandir(path: Any = ".") -> Any:
        if _same_directory(path, session.root.parent):
            raise OSError(errno.EIO, "injected evidence inventory failure")
        return real_scandir(path)

    with monkeypatch.context() as boundary:
        boundary.setattr(os, "listdir", unavailable_listdir)
        boundary.setattr(os, "scandir", unavailable_scandir)
        if command == "status":
            _failure(_invoke(tmp_path, capsys, command), "runtime_format")
        else:
            report = _doctor_payload(tmp_path, capsys)
            repeated = _doctor_payload(tmp_path, capsys)
            reason = _doctor_checks(report)["evidence"]
            assert isinstance(reason, str) and reason.strip()
            assert reason != "available"
            assert reason == _doctor_checks(repeated)["evidence"]
            assert report["ok"] is False
    assert session.raw.read_bytes() == b"retained raw output\n"


def _fail_repeated_snapshot_reads(
    boundary: pytest.MonkeyPatch,
    sessions: Path,
    run_lock: Path,
    unstable_resource: str,
) -> None:
    real_listdir, real_scandir = os.listdir, os.scandir
    real_open, real_io_open = os.open, io.open
    observations = 0

    def observe(resource: str) -> None:
        nonlocal observations
        if resource == unstable_resource:
            observations += 1
            if observations > 1:
                raise OSError(errno.EIO, "resource unavailable after first snapshot")

    def listdir_once(path: Any = ".") -> Any:
        if _same_directory(path, sessions):
            observe("inventory")
        return real_listdir(path)

    def scandir_once(path: Any = ".") -> Any:
        if _same_directory(path, sessions):
            observe("inventory")
        return real_scandir(path)

    def open_once(path: Any, *args: Any, **kwargs: Any) -> Any:
        if not isinstance(path, int) and Path(path).name == run_lock.name:
            observe("authority")
        return real_open(path, *args, **kwargs)

    def io_open_once(path: Any, *args: Any, **kwargs: Any) -> Any:
        if not isinstance(path, int) and Path(path).name == run_lock.name:
            observe("authority")
        return real_io_open(path, *args, **kwargs)

    boundary.setattr(os, "listdir", listdir_once)
    boundary.setattr(os, "scandir", scandir_once)
    boundary.setattr(os, "open", open_once)
    boundary.setattr(io, "open", io_open_once)


@pytest.mark.parametrize("unstable_resource", ("inventory", "authority"))
def test_doctor_reuses_its_first_evidence_and_liveness_snapshot(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    unstable_resource: str,
) -> None:
    _initialize(tmp_path, capsys)
    paths, _metadata, retained = _session(tmp_path, "retained")
    paths, active_metadata, active = _session(tmp_path, "active")
    publish_run_metadata(paths, active_metadata)

    with RunLock.acquire(paths.run_lock), monkeypatch.context() as boundary:
        _fail_repeated_snapshot_reads(
            boundary, active.root.parent, paths.run_lock, unstable_resource
        )
        report = _doctor_payload(tmp_path, capsys)

    assert _doctor_checks(report)["evidence"] == "available"
    assert _doctor_checks(report)["run"] == "available"
    assert report["ok"] is True
    assert report["purge_preview"]["selected"] == [str(retained.root)]
    assert report["purge_preview"]["total_bytes"] == sum(
        path.stat().st_size for path in retained.root.iterdir() if path.is_file()
    )
    assert active.raw.read_bytes() == b"retained raw output\n"


def _assert_status_evidence(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    session: Any,
    session_id: str,
) -> None:
    status = _success(_invoke(tmp_path, capsys, "status"))
    evidence = status["evidence"]
    settings = runtime_settings(tmp_path)
    assert evidence["max_retained_bytes"] == settings.max_retained_bytes
    assert evidence["min_free_bytes"] == settings.min_free_bytes
    assert (
        evidence["total_bytes"]
        >= session.raw.stat().st_size + session.normalized.stat().st_size
    )
    assert len(evidence["sessions"]) == 1
    assert set(evidence["sessions"][0]) == {
        "session_id",
        "path",
        "size_bytes",
        "modified_at",
        "active",
        "device",
        "inode",
    }
    assert evidence["sessions"][0]["session_id"] == session_id


@pytest.mark.parametrize("command", ("status", "doctor"))
@pytest.mark.parametrize("session_id", ("nightly-retained-run", "operator-repro-42"))
def test_diagnostics_report_evidence_and_an_executable_purge_preview(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    session_id: str,
    monkeypatch: pytest.MonkeyPatch,
    command: str,
) -> None:
    runtime = _initialize(tmp_path, capsys)
    _paths, _metadata, session = _session(tmp_path, session_id)
    payload = _success(_invoke(tmp_path, capsys, command))
    if command == "doctor":
        _assert_doctor_report(payload, runtime)
    else:
        assert payload["evidence"]["runtime_root"] == str(runtime)
        assert payload["evidence"]["sessions"][0]["path"] == str(session.root)
    preview = payload["purge_preview"]
    assert set(preview) == {
        "schema_version",
        "applied",
        "selected",
        "total_bytes",
        "command",
    }
    assert preview["schema_version"] == 1
    assert preview["applied"] is False
    assert preview["selected"] == [str(session.root)]
    assert preview["total_bytes"] > 0
    argv = preview["command"]
    assert isinstance(argv, list)
    assert all(isinstance(argument, str) for argument in argv)
    assert argv[0] == "ovcaq"
    assert argv.count("--root") == 1
    assert argv[argv.index("--root") + 1] == str(tmp_path)
    assert argv[argv.index("logs") + 1] == "purge"
    assert "--apply" not in argv
    build_parser().parse_args(argv[1:])
    _assert_status_evidence(tmp_path, capsys, session, session_id)
    unrelated_cwd = tmp_path / "unrelated-cwd"
    unrelated_cwd.mkdir()
    monkeypatch.chdir(unrelated_cwd)
    preview_code = main(["--json", *argv[1:]])
    captured = capsys.readouterr()
    round_trip = _success((preview_code, captured.out, captured.err))
    assert round_trip["selected"] == preview["selected"]
    assert round_trip["total_bytes"] == preview["total_bytes"]
    assert round_trip["applied"] is False
    assert session.raw.read_bytes() == b"retained raw output\n"


def test_doctor_surfaces_failed_and_unsupported_probe_facts_and_unhealthy_aggregate(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _initialize(tmp_path, capsys)
    facts = (
        CapabilityResult(
            "process_group", "unsupported", "process grouping unavailable"
        ),
        CapabilityResult("advisory_lock", "failed", "exclusive lock probe failed"),
    )
    with patch("ovcaq.cli.probe_platform", autospec=True, return_value=facts):
        _code, stdout, stderr = _invoke(tmp_path, capsys, "doctor")
    assert stderr == ""
    payload = json.loads(stdout)
    assert payload["ok"] is False
    assert payload["capabilities"] == [
        {
            "name": "advisory_lock",
            "status": "failed",
            "detail": "exclusive lock probe failed",
        },
        {
            "name": "process_group",
            "status": "unsupported",
            "detail": "process grouping unavailable",
        },
    ]


def test_doctor_reports_process_identity_fact(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _initialize(tmp_path, capsys)
    live = process_identity(os.getpid())
    assert live is not None
    report = _doctor_payload(tmp_path, capsys)
    facts = {entry["name"]: entry for entry in report["capabilities"]}
    assert facts["process_identity"] == {
        "name": "process_identity",
        "status": "supported",
        "detail": live.started,
    }

    degraded = (
        CapabilityResult("process_group", "supported", "Isolation verified"),
        CapabilityResult("process_identity", "degraded", "probe returned no identity"),
    )
    with patch("ovcaq.cli.probe_platform", autospec=True, return_value=degraded):
        _code, stdout, stderr = _invoke(tmp_path, capsys, "doctor")
    assert stderr == ""
    payload = json.loads(stdout)
    assert payload["ok"] is False
    assert payload["capabilities"] == [
        {
            "name": "process_group",
            "status": "supported",
            "detail": "Isolation verified",
        },
        {
            "name": "process_identity",
            "status": "degraded",
            "detail": "probe returned no identity",
        },
    ]


def _emergency(paths: Any) -> None:
    def unwritable_state(*_args: Any, **_kwargs: Any) -> None:
        raise OSError("test state persistence failure")

    record_state_failure(
        paths,
        site="test-runtime-cli",
        detail="retained recovery detail",
        write_state_notice=unwritable_state,
    )


@pytest.mark.parametrize("state_health", ("available", "missing", "invalid"))
def test_emergency_acknowledgement_validates_state_and_archives_only_after_recovery(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], state_health: str
) -> None:
    runtime = _initialize(tmp_path, capsys)
    paths, _metadata, _session_paths = _session(tmp_path, "session-1")
    _emergency(paths)
    marker = runtime / "state-write-failed.json"
    before = marker.read_bytes()
    if state_health == "missing":
        (runtime / "state.json").unlink()
    elif state_health == "invalid":
        (runtime / "state.json").write_bytes(b"{invalid-state")
    status = _success(_invoke(tmp_path, capsys, "status"))
    attention = json.dumps(status["attention"])
    assert str(marker) in attention
    assert "retained recovery detail" in attention
    assert marker.read_bytes() == before
    result = _invoke(tmp_path, capsys, "doctor", "--acknowledge-emergency")
    if state_health == "available":
        report = _success(result)
        assert report["ok"] is True
        archive_value = report["acknowledged_emergency_archive"]
        assert isinstance(archive_value, str)
        archive = Path(archive_value)
        assert archive.is_absolute()
        assert archive.parent == runtime / "reports"
        assert archive.name.startswith("emergency-") and archive.suffix == ".json"
        assert archive.read_bytes() == before
        assert archive.stat().st_mode & 0o777 == 0o600
        assert not marker.exists()
        archived = [
            path
            for path in runtime.rglob("*")
            if path.is_file() and path.read_bytes() == before
        ]
        assert archived == [archive]
        assert (
            _doctor_payload(tmp_path, capsys)["acknowledged_emergency_archive"] is None
        )
        recovered_status = _success(_invoke(tmp_path, capsys, "status"))
        assert set(recovered_status) == set(status)
        assert "acknowledged_emergency_archive" not in recovered_status
    else:
        assert result[0] != 0
        assert "Traceback" not in "".join(result[1:])
        assert marker.read_bytes() == before


@pytest.mark.parametrize(
    "damage", ["deep", "malformed", "duplicate", "oversized", "future"]
)
def test_doctor_rejects_invalid_emergency_evidence_without_a_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], damage: str
) -> None:
    runtime = _initialize(tmp_path, capsys)
    _emergency(resolve_runtime_paths(tmp_path))
    marker = runtime / "state-write-failed.json"
    original = marker.read_bytes()
    if damage == "deep":
        evidence = b"[" * 2000 + b"0" + b"]" * 2000
    elif damage == "malformed":
        evidence = b'{"schema_version":'
    elif damage == "duplicate":
        evidence = original.rstrip()[:-1] + b', "schema_version": 1}'
    elif damage == "oversized":
        evidence = original.ljust(MAX_STATE_BYTES + 1, b" ")
    else:
        evidence = json.dumps(json.loads(original) | {"schema_version": 999}).encode()
    marker.write_bytes(evidence)

    _failure(
        _invoke(tmp_path, capsys, "doctor", "--acknowledge-emergency"),
        "runtime_format",
    )
    assert marker.read_bytes() == evidence
    assert list((runtime / "reports").glob("emergency-*.json")) == []


def _deny_repeated_state_read(state: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_open, real_io_open, real_builtin_open = os.open, io.open, builtins.open
    state_reads = 0

    def deny_repeated_read(path: Any) -> None:
        nonlocal state_reads
        if not isinstance(path, int) and Path(path).name == state.name:
            state_reads += 1
            if state_reads > 1:
                raise OSError(errno.EIO, "state unavailable after first read")

    def open_once(path: Any, flags: int, *args: Any, **kwargs: Any) -> Any:
        if not flags & os.O_WRONLY:
            deny_repeated_read(path)
        return real_open(path, flags, *args, **kwargs)

    def io_open_once(path: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        if "r" in mode or "+" in mode:
            deny_repeated_read(path)
        return real_io_open(path, mode, *args, **kwargs)

    def builtin_open_once(path: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        if "r" in mode or "+" in mode:
            deny_repeated_read(path)
        return real_builtin_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(os, "open", open_once)
    monkeypatch.setattr(io, "open", io_open_once)
    monkeypatch.setattr(builtins, "open", builtin_open_once)


def test_emergency_acknowledgement_succeeds_when_state_cannot_be_read_twice(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = _initialize(tmp_path, capsys)
    paths, _metadata, _session_paths = _session(tmp_path, "session-1")
    _emergency(paths)
    marker = runtime / "state-write-failed.json"
    marker_bytes = marker.read_bytes()
    state = runtime / "state.json"
    state_bytes = state.read_bytes()
    with monkeypatch.context() as boundary:
        _deny_repeated_state_read(state, boundary)
        report = _success(
            _invoke(tmp_path, capsys, "doctor", "--acknowledge-emergency")
        )

    assert report["ok"] is True
    assert report["attention"] is None
    assert _doctor_checks(report)["state"] == "available"
    assert not marker.exists()
    assert state.read_bytes() == state_bytes
    archives = [
        path
        for path in runtime.rglob("*")
        if path.is_file() and path.read_bytes() == marker_bytes
    ]
    assert len(archives) == 1
    assert report["acknowledged_emergency_archive"] == str(archives[0])


@pytest.mark.parametrize("selector", ("session", "before"))
def test_purge_previews_without_mutation_and_applies_only_selected_sessions(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], selector: str
) -> None:
    _initialize(tmp_path, capsys)
    _paths, _metadata, old = _session(tmp_path, "old", "2026-01-01T00:00:00Z")
    _paths, _metadata, recent = _session(tmp_path, "recent", "2026-03-01T00:00:00Z")
    os.utime(old.root, (1_767_225_600, 1_767_225_600))
    os.utime(recent.root, (1_772_323_200, 1_772_323_200))
    for path in old.root.iterdir():
        os.utime(path, (1_767_225_600, 1_767_225_600))
    for path in recent.root.iterdir():
        os.utime(path, (1_772_323_200, 1_772_323_200))
    arguments = (
        ("--session", "old")
        if selector == "session"
        else ("--before", "2026-02-01T00:00:00Z")
    )
    retained = {
        str(path): path.read_bytes() for path in old.root.rglob("*") if path.is_file()
    }
    preview = _success(_invoke(tmp_path, capsys, "logs", "purge", *arguments))
    assert set(preview) == {
        "schema_version",
        "applied",
        "selected",
        "total_bytes",
        "command",
    }
    assert preview["schema_version"] == 1
    assert preview["applied"] is False
    assert preview["selected"] == [str(old.root)]
    assert preview["total_bytes"] == sum(map(len, retained.values()))
    assert preview["command"][-1] == "--apply"
    assert all(isinstance(argument, str) for argument in preview["command"])
    assert "logs" in preview["command"]
    assert "purge" in preview["command"]
    assert all(argument in preview["command"] for argument in arguments)
    assert {
        str(path): path.read_bytes() for path in old.root.rglob("*") if path.is_file()
    } == retained
    apply_code = main(["--json", *preview["command"][1:]])
    captured = capsys.readouterr()
    applied = _success((apply_code, captured.out, captured.err))
    assert applied["applied"] is True
    assert applied["selected"] == preview["selected"]
    assert not old.root.exists()
    assert recent.raw.read_bytes() == b"retained raw output\n"


def test_purge_apply_preserves_an_active_session_and_reports_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _initialize(tmp_path, capsys)
    paths, metadata, session = _session(tmp_path, "active")
    publish_run_metadata(paths, metadata)
    with RunLock.acquire(paths.run_lock):
        result = _invoke(
            tmp_path, capsys, "logs", "purge", "--session", "active", "--apply"
        )
    assert result[0] != 0
    assert result[1] == ""
    failure = json.loads(result[2])
    assert set(failure) == {"ok", "error"}
    assert failure["ok"] is False
    assert set(failure["error"]) == {"code", "message", "path"}
    assert failure["error"]["code"] != "usage"
    assert "Traceback" not in result[2]
    assert session.raw.read_bytes() == b"retained raw output\n"


def test_human_purge_keeps_requested_data_on_stdout_and_mutation_text_on_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _initialize(tmp_path, capsys)
    _paths, _metadata, session = _session(tmp_path, "session-1")
    preview = _invoke(
        tmp_path, capsys, "logs", "purge", "--session", "session-1", json_mode=False
    )
    assert preview[0] == 0
    assert str(session.root) in preview[1]
    assert "--apply" in preview[1]
    assert preview[2] == ""
    applied = _invoke(
        tmp_path,
        capsys,
        "logs",
        "purge",
        "--session",
        "session-1",
        "--apply",
        json_mode=False,
    )
    assert applied[0] == 0
    assert str(session.root) in applied[1]
    assert applied[2].strip()
    assert "Traceback" not in applied[2]
    assert not session.root.exists()


def test_explicit_human_follow_streams_bytes_and_interrupt_exits_130(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _initialize(tmp_path, capsys)
    _paths, _metadata, session_paths = _session(tmp_path, "session-1")
    output = tmp_path / "follow-output"
    error = tmp_path / "follow-error"
    with output.open("wb") as stdout, error.open("wb") as stderr:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "ovcaq",
                "--root",
                str(tmp_path),
                "logs",
                "--session",
                "session-1",
                "--follow",
            ],
            stdout=stdout,
            stderr=stderr,
        )
        try:
            deadline = time.monotonic() + 10
            while (
                b"retained raw output\n" not in output.read_bytes()
                and time.monotonic() < deadline
            ):
                assert process.poll() is None, error.read_text()
                time.sleep(0.02)
            assert b"retained raw output\n" in output.read_bytes()
            with session_paths.raw.open("ab") as evidence:
                evidence.write(b"arrived after follower startup\n")
                evidence.flush()
            deadline = time.monotonic() + 10
            while (
                b"arrived after follower startup\n" not in output.read_bytes()
                and time.monotonic() < deadline
            ):
                assert process.poll() is None, error.read_text()
                time.sleep(0.02)
            assert b"arrived after follower startup\n" in output.read_bytes()
            process.send_signal(signal.SIGINT)
            assert process.wait(timeout=5) == 130
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
    assert "Traceback" not in error.read_text()
