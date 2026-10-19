from __future__ import annotations

import json
import select
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
from packaging_support import (
    InstalledWheel,
    assert_installed,
    identity,
    initialize_installed_state,
)
from rework_11_scripts import INITIALIZE_STATE
from rework_12_scripts import ANCESTRY_ACTOR, ORIGIN_CHECK

PRD = "00004-a.md"


def _prepare(installed: InstalledWheel, tmp_path: Path) -> Path:
    script = (
        INITIALIZE_STATE + ORIGIN_CHECK + "\nprint(json.dumps(installed_origins()))\n"
    )
    project, _ = initialize_installed_state(installed, tmp_path, script, PRD, "ovcaq")
    (project / "record.json").write_text('{"op_id": "crash-one"}', encoding="utf-8")
    assert not (project / "new").exists()
    return project


def _state_bytes(project: Path) -> dict[str, bytes | None]:
    state = project / "independent/state.json"
    backup = state.with_suffix(".json.bak")
    return {
        "state": state.read_bytes(),
        "backup": backup.read_bytes() if backup.exists() else None,
    }


def _command(
    installed: InstalledWheel, project: Path, target: str, mode: str
) -> list[str]:
    return [
        str(installed.python),
        "-I",
        "-c",
        ANCESTRY_ACTOR,
        str(project),
        target,
        mode,
    ]


def _invoke(
    installed: InstalledWheel, project: Path, target: str, mode: str, expected: int = 0
) -> dict[str, Any]:
    result = subprocess.run(
        _command(installed, project, target, mode),
        cwd=project,
        env=installed.environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert result.returncode == expected, (result.stdout, result.stderr)
    value: dict[str, Any] = json.loads(result.stdout)
    assert_installed(value["origins"], installed, "ovcaq.workflow.records")
    return value


def _assert_confirmed(value: dict[str, Any], project: Path) -> None:
    confirmations = {entry["path"]: entry["identity"] for entry in value["fsyncs"]}
    for parent in (project, project / "new", project / "new/nested"):
        assert str(parent) in confirmations, (str(parent), value)
        assert confirmations[str(parent)] == identity(parent)


def _assert_one_record(project: Path) -> bytes:
    ledger = project / "new/nested/deferred/batch-deferred.json"
    content = ledger.read_bytes()
    value = json.loads(content)
    assert value["batch_id"] == "batch"
    assert len(value["items"]) == 1
    assert value["items"][0]["op_id"] == "crash-one"
    assert value["items"][0]["prd"] == PRD
    return content


@contextmanager
def _actor(
    installed: InstalledWheel, project: Path, target: str, mode: str
) -> Iterator[subprocess.Popen[str]]:
    process = subprocess.Popen(
        _command(installed, project, target, mode),
        cwd=project,
        env=installed.environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        yield process
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=10)


def _await_event(
    installed: InstalledWheel, process: subprocess.Popen[str], event: str
) -> dict[str, Any]:
    assert process.stdout is not None
    ready, _, _ = select.select([process.stdout], [], [], 10)
    assert ready, f"actor did not reach {event}; status={process.poll()}"
    line = process.stdout.readline()
    assert line, f"actor exited before {event}; status={process.poll()}"
    value: dict[str, Any] = json.loads(line)
    assert value["event"] == event, value
    assert_installed(value["origins"], installed, "ovcaq.workflow.records")
    return value


def _finish(
    installed: InstalledWheel, process: subprocess.Popen[str], expected: int = 0
) -> dict[str, Any]:
    stdout, stderr = process.communicate(input="continue\n", timeout=20)
    assert process.returncode == expected, (stdout, stderr)
    value: dict[str, Any] = json.loads(stdout)
    assert value["exit"] == expected, value
    assert_installed(value["origins"], installed, "ovcaq.workflow.records")
    return value


@pytest.mark.parametrize("target", ("new", "new/nested"))
def test_installed_retry_and_replay_confirm_ancestry_after_abrupt_exit(
    installed_wheel: InstalledWheel, tmp_path: Path, target: str
) -> None:
    project = _prepare(installed_wheel, tmp_path)
    authoritative = _state_bytes(project)
    interrupted = _invoke(installed_wheel, project, target, "crash", expected=73)
    directory = project / target
    assert interrupted["event"] == "exit-before-parent-fsync"
    assert interrupted["target"] == str(directory)
    assert directory.is_dir()
    assert interrupted["identity"] == identity(directory)
    assert interrupted["parent_identity"] == identity(directory.parent)
    assert _state_bytes(project) == authoritative
    assert not (project / "new/nested/deferred/batch-deferred.json").exists()

    retry = _invoke(installed_wheel, project, target, "retry")
    _assert_confirmed(retry, project)
    assert identity(directory) == interrupted["identity"]
    assert _state_bytes(project) == authoritative
    ledger_after_retry = _assert_one_record(project)

    replay = _invoke(installed_wheel, project, target, "replay")
    _assert_confirmed(replay, project)
    assert identity(directory) == interrupted["identity"]
    assert _state_bytes(project) == authoritative
    assert _assert_one_record(project) == ledger_after_retry


@pytest.mark.parametrize("fail_confirmation", (False, True))
def test_installed_concurrent_creation_confirms_and_preserves_peer_directory(
    installed_wheel: InstalledWheel, tmp_path: Path, fail_confirmation: bool
) -> None:
    project = _prepare(installed_wheel, tmp_path)
    authoritative = _state_bytes(project)
    mode = "racer-fail" if fail_confirmation else "racer"
    with _actor(installed_wheel, project, "new", mode) as racer:
        _await_event(installed_wheel, racer, "before-mkdir")
        assert not (project / "new").exists()
        with _actor(installed_wheel, project, "new", "peer") as peer:
            created = _await_event(installed_wheel, peer, "peer-created")
            assert (project / "new").is_dir()
            assert identity(project / "new") == created["identity"]
            result = _finish(installed_wheel, racer, 2 if fail_confirmation else 0)
            assert result["peer_seen"] == created["identity"]
            assert result["failed_parent"] is fail_confirmation
            assert {"path": str(project), "identity": identity(project)} in result[
                "fsyncs"
            ]
            assert (project / "new").is_dir()
            assert identity(project / "new") == created["identity"]
            assert _state_bytes(project) == authoritative
            if fail_confirmation:
                assert "injected peer parent fsync failure" in result["error"]
            completed = _finish(installed_wheel, peer)
            assert completed["path"] == str(
                project / "new/nested/deferred/batch-deferred.json"
            )
    assert _state_bytes(project) == authoritative
    assert identity(project / "new") == created["identity"]
    ledger_after_callers = _assert_one_record(project)
    replay = _invoke(installed_wheel, project, "new", "replay")
    _assert_confirmed(replay, project)
    assert _state_bytes(project) == authoritative
    assert _assert_one_record(project) == ledger_after_callers
