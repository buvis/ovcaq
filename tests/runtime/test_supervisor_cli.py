from __future__ import annotations

import argparse
import json
import os
import signal
import stat
import subprocess
import sys
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from ovcaq.cli import build_parser, command_inventory, main, render_command_reference
from ovcaq.config import supervisor_settings
from ovcaq.runtime.registry import (
    FleetEntry,
    FleetRegistry,
    FleetRun,
    ProcessIdentity,
    RegistrySnapshot,
    process_identity,
)
from ovcaq.runtime.session import RunObservation, SessionMetadata, publish_run_metadata
from ovcaq.state.store import StateError
from ovcaq.supervisor_cli import (
    LaunchedSupervisor,
    LaunchError,
    LaunchFailureEvidence,
    launch_supervisor,
    stop_supervisor,
)
from ovcaq.tui.app import RunControlService, StaleSelectionError


@pytest.fixture(autouse=True)
def isolated_homes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "xdg-state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))


def _invoke(
    root: Path, capsys: pytest.CaptureFixture[str], *arguments: str
) -> tuple[int, str, str]:
    result = main(["--root", str(root), "--json", *arguments])
    captured = capsys.readouterr()
    return result, captured.out, captured.err


def _success(result: tuple[int, str, str]) -> dict[str, Any]:
    code, stdout, stderr = result
    assert code == 0, stderr
    assert stderr == ""
    payload = json.loads(stdout)
    assert isinstance(payload, dict)
    return payload


def _failure(result: tuple[int, str, str]) -> dict[str, Any]:
    code, stdout, stderr = result
    assert code != 0
    assert stdout == ""
    assert "Traceback" not in stderr
    payload = json.loads(stderr)
    assert set(payload) == {"ok", "error"}
    assert payload["ok"] is False
    assert set(payload["error"]) == {"code", "message", "path"}
    assert isinstance(payload["error"]["code"], str) and payload["error"]["code"]
    assert isinstance(payload["error"]["message"], str) and payload["error"]["message"]
    assert payload["error"]["path"] is None or isinstance(payload["error"]["path"], str)
    return payload


def _state(root: Path) -> dict[str, Any]:
    return json.loads(
        (root / "docs/dev/project-management/ovcaq/state.json").read_text()
    )


def test_parser_inventory_and_reference_expose_the_same_lifecycle_commands() -> None:
    parser = build_parser()
    for arguments in (
        ["run"],
        ["run", "--no-tui"],
        ["run", "--no-tui", "--agent", "claude"],
        ["attach"],
        ["attach", "--run-id", "selected"],
        ["--root", "/project", "attach", "--run-id", "selected"],
        ["pause"],
        ["pause", "--reason", "maintenance"],
        ["resume"],
        ["stop"],
        ["capability", "retry", "agoge"],
    ):
        parser.parse_args(arguments)
    inventory = command_inventory(parser)
    assert any(
        " run" in line and "--no-tui" in line and "--agent" in line
        for line in inventory
    )
    assert any(" pause" in line and "--reason" in line for line in inventory)
    assert any(" attach" in line and "--run-id" in line for line in inventory)
    for command in (" resume", " stop", " capability retry"):
        assert any(command in line for line in inventory)
    rendered = render_command_reference(parser)
    assert (
        tuple(line for line in rendered.splitlines() if line.startswith("ovcaq "))
        == inventory
    )
    reference = Path(__file__).resolve().parents[2] / "docs/operations.md"
    assert reference.read_text(encoding="utf-8") == rendered


def test_parser_exposes_init_state_and_workflow_command_inventory() -> None:
    parser = build_parser()
    subparsers = [
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ]

    assert len(subparsers) == 1
    assert tuple(subparsers[0].choices) == (
        "init",
        "state",
        "workflow",
        "status",
        "doctor",
        "logs",
        "run",
        "attach",
        "pause",
        "resume",
        "stop",
        "capability",
    )


@pytest.mark.parametrize("reason", [None, "maintenance: café"])
def test_pause_commits_boundary_intent_and_resume_clears_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], reason: str | None
) -> None:
    _success(_invoke(tmp_path, capsys, "init"))
    before = _state(tmp_path)
    arguments = () if reason is None else ("--reason", reason)
    paused = _success(_invoke(tmp_path, capsys, "pause", *arguments))
    assert set(paused) == {"ok", "revision", "result"}
    assert paused["ok"] is True
    state = _state(tmp_path)
    assert paused["result"] == state
    assert paused["revision"] == state["revision"] > before["revision"]
    assert state["control"]["pause_requested"] is True
    if reason is None:
        assert state["control"]["pause_reason"] is None
    else:
        record = state["control"]["pause_reason"]
        assert set(record) == {"site", "detail", "created_at"}
        assert record["site"] == "operator" and record["detail"] == reason
        datetime.fromisoformat(record["created_at"])
    assert state["work"] == before["work"]
    resumed = _success(_invoke(tmp_path, capsys, "resume"))
    assert set(resumed) == {"ok", "revision", "result"}
    assert resumed["ok"] is True
    after = _state(tmp_path)
    assert resumed["result"] == after
    assert resumed["revision"] == after["revision"] > state["revision"]
    assert after["control"]["pause_requested"] is False
    assert after["control"]["pause_reason"] is None
    assert after["work"] == before["work"]


@pytest.mark.parametrize(
    ("arguments", "required_argument"),
    [
        pytest.param(
            ("capability", "retry"),
            "name",
            id="capability-retry-requires-name",
        ),
    ],
)
def test_incomplete_lifecycle_commands_fail_with_json_usage_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    arguments: tuple[str, ...],
    required_argument: str,
) -> None:
    _success(_invoke(tmp_path, capsys, "init"))
    before = _state(tmp_path)
    failure = _failure(_invoke(tmp_path, capsys, *arguments))
    assert failure["error"]["code"] == "usage"
    assert required_argument in failure["error"]["message"].lower()
    assert _state(tmp_path) == before


def test_stop_without_published_identity_fails_closed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _success(_invoke(tmp_path, capsys, "init"))
    before = _state(tmp_path)
    first = _failure(_invoke(tmp_path, capsys, "stop"))
    second = _failure(_invoke(tmp_path, capsys, "stop"))
    assert first["error"]["code"] == second["error"]["code"] != "usage"
    assert _state(tmp_path) == before


@dataclass
class SelectedRun:
    run: FleetRun
    registry: FleetRegistry
    metadata: SessionMetadata
    paths: Any
    signals: list[tuple[int, int]]


@pytest.fixture
def selected_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> SelectedRun:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "xdg-state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))
    _success(_invoke(tmp_path, capsys, "init"))
    paths = supervisor_settings(tmp_path).runtime.paths
    identity = process_identity(os.getpid())
    assert identity is not None
    run = FleetRun(
        "selected",
        tmp_path,
        "generic",
        "2026-10-03T12:00:00Z",
        identity.pid,
        identity.started,
    )
    metadata = SessionMetadata(
        1,
        run.run_id,
        "supervisor",
        run.agent,
        run.pid,
        run.process_start,
        run.started_at,
    )
    publish_run_metadata(paths, metadata)
    registry = FleetRegistry(paths.fleet_root)
    registry.publish(
        FleetEntry(
            1,
            run.root,
            run.pid,
            run.process_start,
            run.run_id,
            run.agent,
            run.started_at,
        )
    )
    signals: list[tuple[int, int]] = []
    monkeypatch.setattr(os, "kill", lambda pid, sig: signals.append((pid, sig)))
    monkeypatch.setattr("ovcaq.supervisor_cli.run_lock_held", lambda *a, **kw: True)
    return SelectedRun(run, registry, metadata, paths, signals)


def test_stop_signals_only_the_exact_fully_validated_supervisor(
    selected_run: SelectedRun,
) -> None:
    run = selected_run.run
    before = _state(run.root)
    result = stop_supervisor(run)
    assert result == ProcessIdentity(run.pid, run.process_start)
    assert selected_run.signals == [(run.pid, signal.SIGTERM)]
    assert _state(run.root) == before


def _invalidate_proof(
    selected_run: SelectedRun, monkeypatch: pytest.MonkeyPatch, mismatch: str
) -> None:
    run = selected_run.run
    if mismatch.startswith("metadata-"):
        field = mismatch.removeprefix("metadata-")
        changed = {
            "run_id": "replacement",
            "pid": run.pid + 1,
            "process_start": "other",
        }
        publish_run_metadata(
            selected_run.paths,
            replace(selected_run.metadata, **{field: changed[field]}),
        )
    elif mismatch == "registry-absent":
        selected_run.registry.remove(run.run_id)
    elif mismatch.startswith("registry-"):
        entry = FleetEntry(
            1,
            run.root,
            run.pid,
            run.process_start,
            run.run_id,
            run.agent,
            run.started_at,
        )
        field = mismatch.removeprefix("registry-")
        changed = {
            "root": run.root / "other",
            "pid": run.pid + 1,
            "process_start": "other",
        }
        selected_run.registry.publish(replace(entry, **{field: changed[field]}))
        monkeypatch.setattr(
            "ovcaq.runtime.registry.process_matches", lambda identity: True
        )
        assert len(selected_run.registry.snapshot().live) == 1
    elif mismatch == "process":
        monkeypatch.setattr(
            "ovcaq.supervisor_cli.process_matches", lambda identity: False
        )
    else:
        monkeypatch.setattr(
            "ovcaq.supervisor_cli.run_lock_held", lambda *a, **kw: False
        )


@pytest.mark.parametrize(
    "mismatch",
    [
        "metadata-run_id",
        "metadata-pid",
        "metadata-process_start",
        "registry-root",
        "registry-pid",
        "registry-process_start",
        "process",
        "lock",
    ],
)
def test_stop_fails_closed_when_any_identity_or_ownership_proof_is_missing(
    selected_run: SelectedRun, monkeypatch: pytest.MonkeyPatch, mismatch: str
) -> None:
    run = selected_run.run
    _invalidate_proof(selected_run, monkeypatch, mismatch)
    before = _state(run.root)
    with pytest.raises((ValueError, RuntimeError, OSError, StateError)):
        stop_supervisor(run)
    assert selected_run.signals == []
    assert _state(run.root) == before


def test_stop_rejects_an_unregistered_run_even_when_metadata_matches(
    selected_run: SelectedRun,
) -> None:
    selected_run.registry.remove(selected_run.run.run_id)
    with pytest.raises((ValueError, RuntimeError, OSError, StateError)):
        stop_supervisor(selected_run.run)
    assert selected_run.signals == []


def test_exact_run_pause_and_resume_use_compare_and_set(
    selected_run: SelectedRun,
) -> None:
    run = selected_run.run
    controls = RunControlService(selected_run.registry)
    before = _state(run.root)
    controls.pause(run, before["revision"], "maintenance")
    paused = _state(run.root)
    assert paused["revision"] > before["revision"]
    assert paused["control"]["pause_requested"] is True
    assert paused["control"]["pause_reason"]["site"] == "operator"
    assert paused["control"]["pause_reason"]["detail"] == "maintenance"
    with pytest.raises(StateError):
        controls.resume(run, before["revision"])
    assert _state(run.root) == paused
    controls.resume(run, paused["revision"])
    resumed = _state(run.root)
    assert resumed["revision"] > paused["revision"]
    assert resumed["control"]["pause_requested"] is False
    assert resumed["control"]["pause_reason"] is None
    assert resumed["work"] == before["work"]
    assert selected_run.signals == []


@pytest.mark.parametrize("action", ["pause", "resume"])
@pytest.mark.parametrize(
    "mismatch",
    [
        "metadata-run_id",
        "metadata-pid",
        "metadata-process_start",
        "registry-absent",
        "registry-root",
        "registry-pid",
        "registry-process_start",
        "process",
        "lock",
    ],
)
def test_stale_selection_before_compare_and_set_leaves_state_untouched(
    selected_run: SelectedRun,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
    mismatch: str,
) -> None:
    run = selected_run.run
    controls = RunControlService(selected_run.registry)
    if action == "resume":
        controls.pause(run, _state(run.root)["revision"])
    _invalidate_proof(selected_run, monkeypatch, mismatch)
    before = _state(run.root)
    with pytest.raises(StaleSelectionError) as caught:
        getattr(controls, action)(run, before["revision"])
    assert caught.value.committed is False
    assert _state(run.root) == before
    assert selected_run.signals == []


@pytest.mark.parametrize("action", ["pause", "resume"])
def test_replacement_during_control_rolls_back_then_reports_stale(
    selected_run: SelectedRun, monkeypatch: pytest.MonkeyPatch, action: str
) -> None:
    run = selected_run.run
    controls = RunControlService(selected_run.registry)
    if action == "resume":
        controls.pause(run, _state(run.root)["revision"], "maintenance")
    before = _state(run.root)
    state_path = selected_run.paths.state_file
    backup_path = state_path.with_name(state_path.name + ".bak")
    original = state_path.read_bytes()
    backup = backup_path.read_bytes() if backup_path.exists() else None
    replace_file = os.replace
    replacements: list[str] = []

    def replace_then_change_owner(source: Any, destination: Any, **kwargs: Any) -> None:
        replace_file(source, destination, **kwargs)
        if Path(destination).name == "state.json" and not replacements:
            replacements.append("committed")
            publish_run_metadata(
                selected_run.paths, replace(selected_run.metadata, run_id="replacement")
            )

    monkeypatch.setattr(os, "replace", replace_then_change_owner)
    with pytest.raises(StaleSelectionError) as caught:
        if action == "pause":
            controls.pause(run, before["revision"], "maintenance")
        else:
            controls.resume(run, before["revision"])
    assert caught.value.committed is False
    assert replacements == ["committed"]
    assert _state(run.root) == before
    assert state_path.read_bytes() == original
    assert (backup_path.read_bytes() if backup_path.exists() else None) == backup
    assert selected_run.signals == []


@dataclass
class FakeChild:
    pid: int = 43210
    exit_code: int | None = None

    def poll(self) -> int | None:
        return self.exit_code


@dataclass
class LaunchBoundary:
    root: Path
    child: FakeChild
    entry: FleetEntry
    entries: tuple[FleetEntry, ...]
    observation: RunObservation
    spawns: list[tuple[tuple[str, ...], dict[str, Any]]]
    report: Path | None = None
    report_text: str | None = None

    def spawn(self, argv: Any, **options: Any) -> FakeChild:
        self.spawns.append((tuple(argv), options))
        self.report = Path(options["env"]["OVCAQ_LAUNCH_REPORT"])
        if self.report_text is not None:
            self.report.write_text(self.report_text, encoding="utf-8")
        return self.child

    def snapshot(self) -> RegistrySnapshot:
        return RegistrySnapshot(self.entries, (), ())


@pytest.fixture
def launch_boundary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> LaunchBoundary:
    child = FakeChild()
    entry = FleetEntry(
        1,
        tmp_path,
        child.pid,
        "start-token",
        "child",
        "generic",
        "2026-10-03T12:00:00Z",
    )
    boundary = LaunchBoundary(
        tmp_path, child, entry, (entry,), RunObservation("active"), []
    )
    monkeypatch.setattr("ovcaq.supervisor_cli.subprocess.Popen", boundary.spawn)
    monkeypatch.setattr("ovcaq.supervisor_cli.FleetRegistry", lambda *a: boundary)
    monkeypatch.setattr(
        "ovcaq.supervisor_cli.observe_run", lambda *a: boundary.observation
    )
    monkeypatch.setattr(
        "ovcaq.supervisor_cli.process_identity",
        lambda pid: ProcessIdentity(pid, "start-token"),
    )
    ticks = iter(float(number) for number in range(100))
    monkeypatch.setattr("ovcaq.supervisor_cli.time.monotonic", lambda: next(ticks))
    monkeypatch.setattr("ovcaq.supervisor_cli.time.sleep", lambda seconds: None)
    return boundary


@pytest.mark.parametrize("agent", [None, "configured-agent"])
@pytest.mark.parametrize("prefix", [None, ("custom python", "-I", "-m", "ovcaq")])
def test_launch_detaches_exact_child_with_literal_argv_and_private_report(
    launch_boundary: LaunchBoundary,
    agent: str | None,
    prefix: tuple[str, ...] | None,
) -> None:
    boundary = launch_boundary
    options_for_launch = {} if prefix is None else {"argv_prefix": prefix}
    launched = launch_supervisor(boundary.root, agent=agent, **options_for_launch)
    assert isinstance(launched, LaunchedSupervisor)
    entry = boundary.entry
    assert launched.run == FleetRun(
        entry.run_id,
        entry.root,
        entry.agent,
        entry.started_at,
        entry.pid,
        entry.process_start,
    )
    assert len(boundary.spawns) == 1
    argv, options = boundary.spawns[0]
    expected = (prefix or (sys.executable, "-m", "ovcaq")) + (
        "--root",
        str(boundary.root),
        "run",
        "--no-tui",
    )
    assert argv == expected + (() if agent is None else ("--agent", agent))
    for name in ("stdin", "stdout", "stderr"):
        assert options[name] == subprocess.DEVNULL
    assert options["shell"] is False
    assert options["start_new_session"] is True
    assert options["close_fds"] is True
    assert boundary.report is not None
    runtime = supervisor_settings(boundary.root).runtime.paths.runtime_root
    assert boundary.report.is_relative_to(runtime)
    assert stat.S_IMODE(runtime.stat().st_mode) == 0o700
    assert not boundary.report.exists()
    assert boundary.child.poll() is None


@pytest.mark.parametrize(
    "mismatch",
    [
        "zero",
        "multiple",
        "duplicate",
        "unrelated",
        "start-token",
        "root",
        "idle",
        "inconsistent",
    ],
)
def test_launch_rejects_ambiguous_or_unrelated_identity_without_replacement(
    launch_boundary: LaunchBoundary,
    mismatch: str,
) -> None:
    boundary = launch_boundary
    entry = boundary.entry
    if mismatch == "zero":
        boundary.entries = ()
    elif mismatch == "multiple":
        boundary.entries += (replace(entry, run_id="another", pid=entry.pid + 1),)
    elif mismatch == "duplicate":
        boundary.entries += (replace(entry, run_id="duplicate"),)
    elif mismatch == "unrelated":
        boundary.entries = (replace(entry, pid=entry.pid + 1),)
    elif mismatch == "start-token":
        boundary.entries = (replace(entry, process_start="recycled"),)
    elif mismatch == "root":
        boundary.entries = (replace(entry, root=entry.root / "other"),)
    else:
        boundary.observation = RunObservation(mismatch)  # type: ignore[arg-type]
    with pytest.raises(LaunchError) as caught:
        launch_supervisor(boundary.root, agent=None, timeout_seconds=2)
    assert isinstance(caught.value.evidence, LaunchFailureEvidence)
    assert caught.value.evidence.path == boundary.report
    assert caught.value.evidence.detail
    assert len(boundary.spawns) == 1
    assert boundary.child.poll() is None


@pytest.mark.parametrize("timeout", [0.1, 1.0])
def test_launch_waits_for_exact_child_publication_only_until_configured_deadline(
    launch_boundary: LaunchBoundary,
    monkeypatch: pytest.MonkeyPatch,
    timeout: float,
) -> None:
    boundary = launch_boundary
    clock = [0.0]
    observations: list[float] = []

    def tick() -> float:
        clock[0] += 0.01
        return clock[0]

    def sleep(seconds: float) -> None:
        clock[0] += seconds

    def snapshot() -> RegistrySnapshot:
        observations.append(clock[0])
        ready = len(observations) >= 3 and clock[0] >= 0.2
        return RegistrySnapshot((boundary.entry,) if ready else (), (), ())

    monkeypatch.setattr("ovcaq.supervisor_cli.time.monotonic", tick)
    monkeypatch.setattr("ovcaq.supervisor_cli.time.sleep", sleep)
    monkeypatch.setattr(boundary, "snapshot", snapshot)
    if timeout < 0.2:
        with pytest.raises(LaunchError):
            launch_supervisor(boundary.root, agent=None, timeout_seconds=timeout)
    else:
        launched = launch_supervisor(boundary.root, agent=None, timeout_seconds=timeout)
        assert launched.run.run_id == boundary.entry.run_id
        assert launched.run.pid == boundary.child.pid
        assert launched.run.process_start == boundary.entry.process_start
        assert len(observations) >= 3
        assert 0.2 <= clock[0] < timeout
    assert len(boundary.spawns) == 1


def test_timeout_names_child_and_explicit_attach_stop_recovery(
    launch_boundary: LaunchBoundary,
) -> None:
    boundary = launch_boundary
    boundary.entries = ()
    boundary.observation = RunObservation("idle")
    with pytest.raises(LaunchError) as caught:
        launch_supervisor(boundary.root, agent=None, timeout_seconds=2)
    evidence = caught.value.evidence
    assert evidence.exit_code is None
    assert str(boundary.child.pid) in evidence.detail
    assert "ovcaq attach" in evidence.detail
    assert "ovcaq stop" in evidence.detail
    assert len(evidence.detail.encode("utf-8")) <= 4096
    assert len(boundary.spawns) == 1
    assert boundary.child.poll() is None


@pytest.mark.parametrize(
    "message", [None, "driver disconnected for run unicorn", "clé route is unavailable"]
)
def test_early_exit_preserves_bounded_sanitized_failure_evidence(
    launch_boundary: LaunchBoundary,
    message: str | None,
) -> None:
    boundary = launch_boundary
    boundary.child.exit_code = 23
    boundary.entries = ()
    boundary.report_text = (
        None if message is None else "\x1b[31m" + message + "\x00\r\n" + "é" * 5000
    )
    with pytest.raises(LaunchError) as caught:
        launch_supervisor(boundary.root, agent=None, timeout_seconds=2)
    evidence = caught.value.evidence
    assert evidence.exit_code == 23
    assert evidence.path == boundary.report
    assert 0 < len(evidence.detail.encode("utf-8")) <= 4096
    assert "\x1b" not in evidence.detail and "\x00" not in evidence.detail
    if message is None:
        assert "unhandled" in evidence.detail.lower()
        assert "crash" in evidence.detail.lower()
    else:
        assert message in evidence.detail
    assert len(boundary.spawns) == 1


def test_launch_report_is_private_before_child_runs(
    launch_boundary: LaunchBoundary,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary = launch_boundary
    modes: list[int] = []

    def spawn(argv: Any, **options: Any) -> FakeChild:
        report = Path(options["env"]["OVCAQ_LAUNCH_REPORT"])
        modes.append(stat.S_IMODE(report.stat().st_mode))
        assert report.is_file() and not report.is_symlink()
        return boundary.spawn(argv, **options)

    monkeypatch.setattr("ovcaq.supervisor_cli.subprocess.Popen", spawn)
    launch_supervisor(boundary.root, agent=None)
    assert modes == [0o600]


def test_replaced_report_symlink_never_exposes_outside_content(
    launch_boundary: LaunchBoundary,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary = launch_boundary
    outside = boundary.root / "outside.txt"
    outside.write_text("PRIVATE OUTSIDE CONTENT", encoding="utf-8")
    boundary.child.exit_code = 2
    boundary.entries = ()

    def spawn(argv: Any, **options: Any) -> FakeChild:
        child = boundary.spawn(argv, **options)
        assert boundary.report is not None
        boundary.report.unlink()
        boundary.report.symlink_to(outside)
        return child

    monkeypatch.setattr("ovcaq.supervisor_cli.subprocess.Popen", spawn)
    with pytest.raises(LaunchError) as caught:
        launch_supervisor(boundary.root, agent=None)
    assert "PRIVATE OUTSIDE CONTENT" not in str(caught.value)
    assert "PRIVATE OUTSIDE CONTENT" not in caught.value.evidence.detail
    assert outside.read_text(encoding="utf-8") == "PRIVATE OUTSIDE CONTENT"
    assert len(boundary.spawns) == 1


def test_child_scrubs_report_environment_before_constructing_agent_driver(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _success(_invoke(tmp_path, capsys, "init"))
    (tmp_path / "ovcaq.toml").write_text(
        'agent = "generic"\n[agents.generic]\ncommand = ["python"]\n', encoding="utf-8"
    )
    report = tmp_path / "docs/dev/project-management/ovcaq/launch-report"
    report.touch(mode=0o600)
    monkeypatch.setenv("OVCAQ_LAUNCH_REPORT", str(report))
    observed: list[str | None] = []

    def reject_driver(*args: Any, **kwargs: Any) -> Any:
        observed.append(os.environ.get("OVCAQ_LAUNCH_REPORT"))
        raise RuntimeError("agent construction failed")

    monkeypatch.setattr("ovcaq.supervisor_cli.build_driver", reject_driver)
    assert main(["--root", str(tmp_path), "run", "--no-tui"]) != 0
    assert observed == [None]
    assert "OVCAQ_LAUNCH_REPORT" not in os.environ
    assert "agent construction failed" in report.read_text(encoding="utf-8")
    assert stat.S_IMODE(report.stat().st_mode) == 0o600


@pytest.mark.parametrize("destination", ["outside", "symlink", "traversal"])
def test_child_rejects_outside_report_destination_without_writing_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    destination: str,
) -> None:
    _success(_invoke(tmp_path, capsys, "init"))
    outside = tmp_path / "outside.txt"
    outside.write_text("preserve me", encoding="utf-8")
    report = outside
    if destination == "symlink":
        report = tmp_path / "docs/dev/project-management/ovcaq/launch-report"
        report.symlink_to(outside)
    elif destination == "traversal":
        report = tmp_path / "docs/dev/project-management/ovcaq/../../../outside.txt"
    monkeypatch.setenv("OVCAQ_LAUNCH_REPORT", str(report))
    constructed: list[bool] = []

    def reject_driver(*args: Any, **kwargs: Any) -> Any:
        constructed.append(True)
        raise RuntimeError("must validate report before launching agent")

    monkeypatch.setattr("ovcaq.supervisor_cli.build_driver", reject_driver)
    assert main(["--root", str(tmp_path), "run", "--no-tui"]) != 0
    assert constructed == []
    assert outside.read_text(encoding="utf-8") == "preserve me"


@pytest.mark.parametrize("name", ["agoge", "archive-old"])
def test_retry_unknown_capability_is_a_usage_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], name: str
) -> None:
    _success(_invoke(tmp_path, capsys, "init"))
    state_file = tmp_path / "docs/dev/project-management/ovcaq/state.json"
    before = state_file.read_bytes()
    code, stdout, stderr = _invoke(tmp_path, capsys, "capability", "retry", name)
    failure = _failure((code, stdout, stderr))
    assert code == 1 and "Traceback" not in stdout + stderr
    assert failure["error"]["code"] == "usage"
    assert f"unknown capability: {name}" in failure["error"]["message"]
    assert state_file.read_bytes() == before
