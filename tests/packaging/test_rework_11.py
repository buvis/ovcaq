from __future__ import annotations

import json
import select
import signal
import subprocess
from pathlib import Path

import pytest
from packaging_support import (
    InstalledWheel,
    _run,
    _run_unchecked,
)
from rework_11_scripts import (
    FSYNC_SCENARIO,
    INITIALIZE_STATE,
    INSTALLED_ORIGINS,
    READ_LEDGER,
    REPORT_ACTOR,
    UPDATE_PRD,
)


def _assert_installed_origins(installed: InstalledWheel, cwd: Path) -> None:
    result = _run(
        [installed.python, "-c", INSTALLED_ORIGINS],
        cwd=cwd,
        installed_wheel=installed,
    )
    origins = json.loads(result.stdout)
    assert origins
    assert all("site-packages" in origin for origin in origins.values())


def _initialize(
    installed: InstalledWheel, project: Path, state_path: Path, prd: str
) -> None:
    _run(
        [installed.python, "-c", INITIALIZE_STATE, project, state_path, prd],
        cwd=project.parent,
        installed_wheel=installed,
    )


def _defer_command(
    installed: InstalledWheel,
    project: Path,
    runtime_root: Path,
    state_path: Path,
    record_path: Path,
) -> list[str | Path]:
    return [
        installed.console_script,
        "--root",
        project,
        "--json",
        "workflow",
        "defer",
        "--runtime-root",
        runtime_root,
        "--state",
        state_path,
        "--prd",
        "00004-a.md",
        "--record",
        record_path,
    ]


def _read_ledger(
    installed: InstalledWheel, project: Path, runtime_root: Path
) -> list[dict[str, object]]:
    result = _run(
        [installed.python, "-c", READ_LEDGER, runtime_root],
        cwd=project,
        installed_wheel=installed,
    )
    return json.loads(result.stdout)


def _seed_depth_ledger(
    installed_wheel: InstalledWheel,
    project: Path,
    runtime_root: Path,
    state_path: Path,
) -> tuple[Path, bytes]:
    seed_path = project / "seed.json"
    seed = {"op_id": "seed", "detail": "retained"}
    seed_path.write_text(json.dumps(seed), encoding="utf-8")
    seed_command = _defer_command(
        installed_wheel, project, runtime_root, state_path, seed_path
    )
    _run(seed_command, cwd=project, installed_wheel=installed_wheel)
    ledger_path = runtime_root / "deferred/batch-deferred.json"
    return ledger_path, ledger_path.read_bytes()


def _run_depth_candidate(
    installed_wheel: InstalledWheel,
    project: Path,
    runtime_root: Path,
    state_path: Path,
    depth: int,
) -> tuple[dict[str, object], list[str | Path], subprocess.CompletedProcess[str]]:
    payload: int | dict[str, object] = 0
    for _ in range(depth - 1):
        payload = {"child": payload}
    candidate = {"op_id": f"candidate-{depth}", "payload": payload}
    candidate_path = project / "candidate.json"
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    candidate_command = _defer_command(
        installed_wheel, project, runtime_root, state_path, candidate_path
    )
    appended = _run_unchecked(
        candidate_command, cwd=project, installed_wheel=installed_wheel
    )
    return candidate, candidate_command, appended


def _assert_candidate_within_depth_limit(
    installed_wheel: InstalledWheel,
    project: Path,
    runtime_root: Path,
    ledger_path: Path,
    candidate: dict[str, object],
    candidate_command: list[str | Path],
    appended: subprocess.CompletedProcess[str],
) -> None:
    assert appended.returncode == 0
    assert isinstance(json.loads(appended.stdout), dict)
    assert appended.stderr == ""
    appended_bytes = ledger_path.read_bytes()
    loaded = _read_ledger(installed_wheel, project, runtime_root)
    assert [row["op_id"] for row in loaded] == ["seed", candidate["op_id"]]
    assert loaded[1]["payload"] == candidate["payload"]
    replay = _run(candidate_command, cwd=project, installed_wheel=installed_wheel)
    assert isinstance(json.loads(replay.stdout), dict)
    assert ledger_path.read_bytes() == appended_bytes
    assert _read_ledger(installed_wheel, project, runtime_root) == loaded


def _assert_candidate_exceeds_depth_limit(
    installed_wheel: InstalledWheel,
    project: Path,
    candidate_command: list[str | Path],
    ledger_path: Path,
    seed_bytes: bytes,
    state_path: Path,
    authoritative: bytes,
    appended: subprocess.CompletedProcess[str],
) -> None:
    assert appended.returncode == 11
    assert appended.stdout == ""
    error = json.loads(appended.stderr)["error"]
    assert error["code"] == "resource_limit"
    assert error["message"]
    assert "Traceback" not in appended.stderr
    assert ledger_path.read_bytes() == seed_bytes
    assert state_path.read_bytes() == authoritative
    replay = _run_unchecked(
        candidate_command, cwd=project, installed_wheel=installed_wheel
    )
    assert replay.returncode == 11
    assert json.loads(replay.stderr)["error"]["code"] == "resource_limit"
    assert "Traceback" not in replay.stderr
    assert ledger_path.read_bytes() == seed_bytes
    assert state_path.read_bytes() == authoritative


def _assert_ledger_still_writable(
    installed_wheel: InstalledWheel,
    project: Path,
    runtime_root: Path,
    state_path: Path,
    authoritative: bytes,
    depth: int,
) -> None:
    later_path = project / "later.json"
    later_path.write_text(
        json.dumps({"op_id": f"later-{depth}", "detail": "still writable"}),
        encoding="utf-8",
    )
    _run(
        _defer_command(installed_wheel, project, runtime_root, state_path, later_path),
        cwd=project,
        installed_wheel=installed_wheel,
    )
    final = _read_ledger(installed_wheel, project, runtime_root)
    expected_ids = ["seed", f"later-{depth}"]
    if depth == 30:
        expected_ids.insert(1, "candidate-30")
    assert [row["op_id"] for row in final] == expected_ids
    assert state_path.read_bytes() == authoritative


@pytest.mark.parametrize("depth", (30, 31, 32, 33))
def test_installed_defer_keeps_the_composed_ledger_within_reader_depth_limit(
    installed_wheel: InstalledWheel, tmp_path: Path, depth: int
) -> None:
    project = tmp_path / f"ledger-depth-{depth}"
    state_path = project / "authoritative/state.json"
    runtime_root = project / "runtime"
    _initialize(installed_wheel, project, state_path, "00004-a.md")
    _assert_installed_origins(installed_wheel, project)
    authoritative = state_path.read_bytes()
    ledger_path, seed_bytes = _seed_depth_ledger(
        installed_wheel, project, runtime_root, state_path
    )
    candidate, candidate_command, appended = _run_depth_candidate(
        installed_wheel, project, runtime_root, state_path, depth
    )

    if depth == 30:
        _assert_candidate_within_depth_limit(
            installed_wheel,
            project,
            runtime_root,
            ledger_path,
            candidate,
            candidate_command,
            appended,
        )
    else:
        _assert_candidate_exceeds_depth_limit(
            installed_wheel,
            project,
            candidate_command,
            ledger_path,
            seed_bytes,
            state_path,
            authoritative,
            appended,
        )

    _assert_ledger_still_writable(
        installed_wheel, project, runtime_root, state_path, authoritative, depth
    )


@pytest.mark.parametrize(
    "failure_label",
    ("project-parent", "new-parent", "runtime-root", "deferred-leaf"),
)
def test_installed_defer_retries_every_new_directory_fsync_after_failure(
    installed_wheel: InstalledWheel, tmp_path: Path, failure_label: str
) -> None:
    project = tmp_path / f"fsync-{failure_label}"
    result = _run(
        [installed_wheel.python, "-c", FSYNC_SCENARIO, project, failure_label],
        cwd=tmp_path,
        installed_wheel=installed_wheel,
    )
    evidence = json.loads(result.stdout)
    failed = evidence["failed"]
    assert failed["exit"] == 2
    assert failed["stdout"] == ""
    error = json.loads(failed["stderr"])["error"]
    assert error["code"] == "state_io"
    assert failure_label in error["message"]
    assert "Traceback" not in failed["stderr"]
    assert failure_label in failed["directories"]
    assert failed["delegated_calls"] > 0
    assert evidence["runtime_absent_before"]
    if failure_label != "project-parent":
        assert "new-parent" in evidence["directories_after_failure"]

    expected = evidence["expected"]
    required_after_failure = expected[expected.index(failure_label) :]
    retry = evidence["retry"]
    assert retry["exit"] == 0
    assert retry["stderr"] == ""
    assert all(label in retry["directories"] for label in required_after_failure)
    retry_positions = [
        retry["directories"].index(label) for label in required_after_failure
    ]
    assert retry_positions == sorted(retry_positions)
    assert not evidence["state_changed_while_interrupted"]
    assert evidence["state_valid_after_failure"]
    assert evidence["state_unchanged_after_retry"]

    replay = evidence["replay"]
    assert replay["exit"] == 0
    assert replay["stderr"] == ""
    assert evidence["state_unchanged_after_replay"]
    assert evidence["ledger_unchanged_by_replay"]
    assert evidence["ledger_ids"] == ["durable-one"]
    _assert_installed_origins(installed_wheel, project)


def _set_prd(installed: InstalledWheel, root: Path, state_path: Path, prd: str) -> None:
    _run(
        [installed.python, "-c", UPDATE_PRD, state_path, prd],
        cwd=root,
        installed_wheel=installed,
    )


def _render_command(installed: InstalledWheel, root: Path) -> list[str | Path]:
    return [
        installed.console_script,
        "--root",
        root,
        "--json",
        "workflow",
        "render",
        "report",
    ]


def _assert_retry_error(
    result: subprocess.CompletedProcess[str], report_path: Path
) -> None:
    assert result.returncode == 2
    assert result.stdout == ""
    error = json.loads(result.stderr)["error"]
    assert error["code"] == "state_io"
    assert error["message"] == f"publication busy; retry: {report_path}"
    assert "Traceback" not in result.stderr


def _successful_report_text(
    result: subprocess.CompletedProcess[str], report_path: Path
) -> str:
    assert result.returncode == 0
    assert result.stderr == ""
    text = report_path.read_bytes().decode("utf-8")
    assert json.loads(result.stdout)["text"] == text
    return text


def _seed_overlap_report(
    installed_wheel: InstalledWheel, root: Path, state_path: Path
) -> tuple[list[str | Path], Path]:
    _initialize(installed_wheel, root, state_path, "00003-seed.md")
    _assert_installed_origins(installed_wheel, root)
    command = _render_command(installed_wheel, root)
    before_seed = state_path.read_bytes()
    seed = _run(command, cwd=root, installed_wheel=installed_wheel)
    report_path = Path(json.loads(seed.stdout)["path"])
    seed_text = _successful_report_text(seed, report_path)
    assert state_path.read_bytes() == before_seed
    unrelated = "\n## Operator notes\n\nKeep café and žluťoučký.\n"
    report_path.write_text(seed_text + unrelated, encoding="utf-8")
    _set_prd(installed_wheel, root, state_path, "00004-a.md")
    return command, report_path


def _start_report_actor(
    installed_wheel: InstalledWheel, root: Path
) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [installed_wheel.python, "-c", REPORT_ACTOR, root],
        cwd=root,
        env=installed_wheel.environment,
        text=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _await_actor_ready_and_start_publisher_b(
    installed_wheel: InstalledWheel,
    root: Path,
    state_path: Path,
    command: list[str | Path],
    actor: subprocess.Popen[str],
) -> tuple[bytes, subprocess.Popen[str]]:
    assert actor.stdout is not None
    assert select.select([actor.stdout], [], [], 10)[0], "publisher A not ready"
    assert actor.stdout.readline() == "READY\n"
    _set_prd(installed_wheel, root, state_path, "00005-b.md")
    authoritative = state_path.read_bytes()
    publisher_b = subprocess.Popen(
        [str(part) for part in command],
        cwd=root,
        env=installed_wheel.environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return authoritative, publisher_b


def _completed_process(
    command: list[str | Path],
    process: subprocess.Popen[str],
    stdout: str,
    stderr: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def _publication_or_none(
    result: subprocess.CompletedProcess[str], report_path: Path
) -> str | None:
    if result.returncode != 0:
        return None
    return _successful_report_text(result, report_path)


def _communicate_overlapping_publishers(
    actor: subprocess.Popen[str],
    publisher_b: subprocess.Popen[str],
    command: list[str | Path],
    report_path: Path,
    resumed: list[bool],
) -> tuple[
    subprocess.CompletedProcess[str],
    subprocess.CompletedProcess[str],
    str | None,
    str | None,
]:
    # `resumed` is a mutable out-param: it must reflect whether "continue" was
    # already sent to the actor even if an assertion below raises, so the
    # caller's cleanup does not write "continue" to it a second time.
    try:
        b_stdout, b_stderr = publisher_b.communicate(timeout=2)
        b_result = _completed_process(command, publisher_b, b_stdout, b_stderr)
        b_publication = _publication_or_none(b_result, report_path)
        assert actor.stdin is not None
        actor.stdin.write("continue\n")
        actor.stdin.flush()
        resumed[0] = True
        a_stdout, a_stderr = actor.communicate(timeout=20)
        a_result = _completed_process(command, actor, a_stdout, a_stderr)
        a_publication = _publication_or_none(a_result, report_path)
    except subprocess.TimeoutExpired:
        if publisher_b.poll() is None:
            publisher_b.send_signal(signal.SIGSTOP)
        assert actor.stdin is not None
        actor.stdin.write("continue\n")
        actor.stdin.flush()
        resumed[0] = True
        a_stdout, a_stderr = actor.communicate(timeout=20)
        a_result = _completed_process(command, actor, a_stdout, a_stderr)
        a_publication = _publication_or_none(a_result, report_path)
        if publisher_b.poll() is None:
            publisher_b.send_signal(signal.SIGCONT)
        b_stdout, b_stderr = publisher_b.communicate(timeout=20)
        b_result = _completed_process(command, publisher_b, b_stdout, b_stderr)
        b_publication = _publication_or_none(b_result, report_path)
    return a_result, b_result, a_publication, b_publication


def _assert_overlap_publication_state(
    state_path: Path,
    authoritative: bytes,
    report_path: Path,
    a_result: subprocess.CompletedProcess[str],
    b_result: subprocess.CompletedProcess[str],
) -> None:
    assert state_path.read_bytes() == authoritative
    overlap_text = report_path.read_text(encoding="utf-8")
    assert "## 00003-seed.md\n" in overlap_text
    assert "## Operator notes\n" in overlap_text
    if a_result.returncode == 0:
        assert "## 00004-a.md\n" in overlap_text
    if b_result.returncode == 0:
        assert "## 00005-b.md\n" in overlap_text


def _retry_failed_overlap_publications(
    installed_wheel: InstalledWheel,
    root: Path,
    state_path: Path,
    command: list[str | Path],
    report_path: Path,
    a_result: subprocess.CompletedProcess[str],
    b_result: subprocess.CompletedProcess[str],
    a_publication: str | None,
    b_publication: str | None,
) -> tuple[str | None, str | None]:
    if a_result.returncode != 0:
        _assert_retry_error(a_result, report_path)
        _set_prd(installed_wheel, root, state_path, "00004-a.md")
        before = state_path.read_bytes()
        retried_a = _run(command, cwd=root, installed_wheel=installed_wheel)
        a_publication = _successful_report_text(retried_a, report_path)
        assert state_path.read_bytes() == before
    if b_result.returncode != 0:
        _assert_retry_error(b_result, report_path)
        _set_prd(installed_wheel, root, state_path, "00005-b.md")
        before = state_path.read_bytes()
        retried_b = _run(command, cwd=root, installed_wheel=installed_wheel)
        b_publication = _successful_report_text(retried_b, report_path)
        assert state_path.read_bytes() == before
    else:
        _set_prd(installed_wheel, root, state_path, "00005-b.md")
    return a_publication, b_publication


def _assert_overlap_replay(
    installed_wheel: InstalledWheel,
    root: Path,
    state_path: Path,
    command: list[str | Path],
    report_path: Path,
) -> str:
    before_replay = state_path.read_bytes()
    replay = _run(command, cwd=root, installed_wheel=installed_wheel)
    final_text = _successful_report_text(replay, report_path)
    assert state_path.read_bytes() == before_replay
    final_bytes = report_path.read_bytes()
    exact_replay = _run(command, cwd=root, installed_wheel=installed_wheel)
    assert _successful_report_text(exact_replay, report_path) == final_text
    assert report_path.read_bytes() == final_bytes
    assert state_path.read_bytes() == before_replay
    return final_text


def _assert_overlap_final_report(
    final_text: str,
    a_publication: str | None,
    b_publication: str | None,
    report_path: Path,
) -> None:
    assert a_publication is not None
    assert b_publication is not None
    for heading in (
        "## 00003-seed.md\n",
        "## 00004-a.md\n",
        "## 00005-b.md\n",
    ):
        assert final_text.count(heading) == 1
    assert final_text.count("## Operator notes\n") == 1
    assert "Keep café and žluťoučký." in final_text
    assert final_text.count("## Batch Summary\n") == 1
    assert report_path.read_bytes() == final_text.encode("utf-8")


def test_installed_report_overlap_preserves_every_successful_publication(
    installed_wheel: InstalledWheel, tmp_path: Path
) -> None:
    root = tmp_path / "report-overlap"
    state_path = root / "docs/dev/project-management/ovcaq/state.json"
    command, report_path = _seed_overlap_report(installed_wheel, root, state_path)
    actor = _start_report_actor(installed_wheel, root)
    publisher_b: subprocess.Popen[str] | None = None
    resumed = [False]
    try:
        authoritative, publisher_b = _await_actor_ready_and_start_publisher_b(
            installed_wheel, root, state_path, command, actor
        )
        a_result, b_result, a_publication, b_publication = (
            _communicate_overlapping_publishers(
                actor, publisher_b, command, report_path, resumed
            )
        )
        _assert_overlap_publication_state(
            state_path, authoritative, report_path, a_result, b_result
        )
        a_publication, b_publication = _retry_failed_overlap_publications(
            installed_wheel,
            root,
            state_path,
            command,
            report_path,
            a_result,
            b_result,
            a_publication,
            b_publication,
        )
        final_text = _assert_overlap_replay(
            installed_wheel, root, state_path, command, report_path
        )
        _assert_overlap_final_report(
            final_text, a_publication, b_publication, report_path
        )
    finally:
        if not resumed[0] and actor.poll() is None and actor.stdin is not None:
            actor.stdin.write("continue\n")
            actor.stdin.flush()
        for process in (publisher_b, actor):
            if process is not None and process.poll() is None:
                process.kill()
                process.communicate(timeout=10)
