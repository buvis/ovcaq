from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import pytest

from ovcaq.cli import main
from ovcaq.config import supervisor_settings
from ovcaq.runtime.registry import FleetEntry, FleetRun, RegistrySnapshot
from ovcaq.runtime.session import RunObservation
from ovcaq.supervisor_cli import LaunchedSupervisor, LaunchError, LaunchFailureEvidence
from ovcaq.tui.app import AttachResult


@dataclass
class CliBoundary:
    run: FleetRun
    result: AttachResult = field(default_factory=lambda: AttachResult("detached", 0))
    launches: list[tuple[Path, str | None]] = field(default_factory=list)
    attachments: list[dict[str, Any]] = field(default_factory=list)
    entries: tuple[FleetEntry, ...] = ()
    observation: RunObservation = field(default_factory=lambda: RunObservation("idle"))

    def launch(
        self, root: Path, *, agent: str | None, **kwargs: Any
    ) -> LaunchedSupervisor:
        self.launches.append((root, agent))
        return LaunchedSupervisor(self.run)

    def attach(self, **kwargs: Any) -> AttachResult:
        self.attachments.append(kwargs)
        return self.result

    def snapshot(self) -> RegistrySnapshot:
        return RegistrySnapshot(self.entries, (), ())

    @contextmanager
    def guard_mutation(
        self, validate: Callable[[], object]
    ) -> Iterator[Callable[[], None]]:
        validate()
        yield lambda: validate()


@pytest.fixture
def cli_boundary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CliBoundary:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "xdg-state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))
    monkeypatch.setattr("ovcaq.cli.sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("ovcaq.cli.sys.stdout.isatty", lambda: True)
    run = FleetRun(
        "exact-child", tmp_path, "generic", "2026-10-03T12:00:00Z", 43210, "start-token"
    )
    boundary = CliBoundary(run)
    monkeypatch.setattr("ovcaq.cli.launch_supervisor", boundary.launch)
    monkeypatch.setattr("ovcaq.tui.app.attach", boundary.attach)
    monkeypatch.setattr("ovcaq.cli.FleetRegistry", lambda *a, **kw: boundary)
    monkeypatch.setattr("ovcaq.cli.observe_run", lambda *a, **kw: boundary.observation)
    return boundary


@pytest.mark.parametrize("agent", [None, "selected-agent"])
@pytest.mark.parametrize(
    "reason,exit_code",
    [("detached", 0), ("completed", 0), ("fallback", 0), ("failed", 7)],
)
def test_interactive_run_launches_once_and_returns_exact_viewer_result(
    cli_boundary: CliBoundary,
    agent: str | None,
    reason: Any,
    exit_code: int,
) -> None:
    boundary = cli_boundary
    boundary.result = AttachResult(reason, exit_code)
    args = ["--root", str(boundary.run.root), "run"]
    if agent is not None:
        args += ["--agent", agent]
    assert main(args) == exit_code
    assert boundary.launches == [(boundary.run.root, agent)]
    assert len(boundary.attachments) == 1
    attached = boundary.attachments[0]
    assert attached["root"] == boundary.run.root
    assert attached["run_id"] == boundary.run.run_id
    assert attached["registry"] is boundary


@pytest.mark.parametrize(
    "explicit_root,run_id",
    [(False, None), (False, "selected"), (True, None), (True, "selected")],
)
def test_attach_selects_requested_scope_without_launching(
    cli_boundary: CliBoundary,
    explicit_root: bool,
    run_id: str | None,
) -> None:
    boundary = cli_boundary
    args = ["--root", str(boundary.run.root)] if explicit_root else []
    args += ["attach"]
    if run_id is not None:
        args += ["--run-id", run_id]
    assert main(args) == 0
    assert boundary.launches == []
    assert len(boundary.attachments) == 1
    assert boundary.attachments[0]["root"] == (
        boundary.run.root if explicit_root else None
    )
    assert boundary.attachments[0].get("run_id") == run_id


def test_json_attach_is_rejected_without_viewer_or_launch(
    cli_boundary: CliBoundary,
    capsys: pytest.CaptureFixture[str],
) -> None:
    boundary = cli_boundary
    assert main(["--json", "attach"]) != 0
    captured = capsys.readouterr()
    assert captured.out == ""
    error = json.loads(captured.err)
    assert error["ok"] is False
    assert error["error"]["code"] == "usage"
    assert boundary.launches == []
    assert boundary.attachments == []


def _paused_project(root: Path, capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    assert main(["--root", str(root), "--json", "init"]) == 0
    assert (
        main(["--root", str(root), "--json", "pause", "--reason", "maintenance"]) == 0
    )
    capsys.readouterr()
    return json.loads(
        (root / "docs/dev/project-management/ovcaq/state.json").read_text(
            encoding="utf-8"
        )
    )


def _interactive_streams(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("ovcaq.cli.sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("ovcaq.cli.sys.stdout.isatty", lambda: True)


def test_resume_after_boundary_pause_launches_once_and_attaches_new_identity(
    cli_boundary: CliBoundary,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary = cli_boundary
    before = _paused_project(boundary.run.root, capsys)
    _interactive_streams(monkeypatch)
    assert main(["--root", str(boundary.run.root), "resume"]) == 0
    state = json.loads(
        (boundary.run.root / "docs/dev/project-management/ovcaq/state.json").read_text()
    )
    assert state["revision"] > before["revision"]
    assert state["control"]["pause_requested"] is False
    assert state["control"]["pause_reason"] is None
    assert state["work"] == before["work"]
    assert boundary.launches == [(boundary.run.root, None)]
    assert len(boundary.attachments) == 1
    assert boundary.attachments[0]["run_id"] == boundary.run.run_id
    assert boundary.attachments[0]["root"] == boundary.run.root


@pytest.mark.parametrize(
    "json_mode,stdin_tty,stdout_tty",
    [(False, False, True), (True, True, True), (False, True, False)],
)
def test_noninteractive_resume_only_clears_pause(
    cli_boundary: CliBoundary,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    json_mode: bool,
    stdin_tty: bool,
    stdout_tty: bool,
) -> None:
    boundary = cli_boundary
    before = _paused_project(boundary.run.root, capsys)
    monkeypatch.setattr("ovcaq.cli.sys.stdin.isatty", lambda: stdin_tty)
    monkeypatch.setattr("ovcaq.cli.sys.stdout.isatty", lambda: stdout_tty)
    args = ["--root", str(boundary.run.root)] + (["--json"] if json_mode else [])
    assert main([*args, "resume"]) == 0
    state = json.loads(
        (boundary.run.root / "docs/dev/project-management/ovcaq/state.json").read_text()
    )
    assert state["revision"] > before["revision"]
    assert state["control"]["pause_requested"] is False
    assert state["control"]["pause_reason"] is None
    assert boundary.launches == []
    assert boundary.attachments == []


@pytest.mark.parametrize(
    "no_tui,stdin_tty,stdout_tty,json_mode",
    [
        (True, True, True, False),
        (False, False, True, False),
        (False, True, False, False),
        (True, True, True, True),
    ],
)
def test_noninteractive_run_dispatches_foreground_without_detached_launch(
    cli_boundary: CliBoundary,
    monkeypatch: pytest.MonkeyPatch,
    no_tui: bool,
    stdin_tty: bool,
    stdout_tty: bool,
    json_mode: bool,
) -> None:
    boundary = cli_boundary
    calls: list[Path] = []

    def foreground(args: Any, root: Path, **kwargs: Any) -> tuple[Any, Any, bool, int]:
        calls.append(root)
        return {"ok": True}, None, False, 9

    monkeypatch.setattr("ovcaq.cli.dispatch_supervisor", foreground)
    monkeypatch.setattr("ovcaq.cli.sys.stdin.isatty", lambda: stdin_tty)
    monkeypatch.setattr("ovcaq.cli.sys.stdout.isatty", lambda: stdout_tty)
    args = ["--root", str(boundary.run.root)] + (["--json"] if json_mode else [])
    args += ["run"] + (["--no-tui"] if no_tui else [])
    assert main(args) == 9
    assert calls == [boundary.run.root]
    assert boundary.launches == []
    assert boundary.attachments == []


def test_json_run_requires_explicit_foreground_opt_in(
    cli_boundary: CliBoundary,
    capsys: pytest.CaptureFixture[str],
) -> None:
    boundary = cli_boundary
    assert main(["--root", str(boundary.run.root), "--json", "run"]) != 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err)["error"]["code"] == "usage"
    assert boundary.launches == []
    assert boundary.attachments == []


@pytest.mark.parametrize("ambiguous", [False, True])
def test_resume_revalidates_live_selected_run_then_attaches_without_launch(
    cli_boundary: CliBoundary,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    ambiguous: bool,
) -> None:
    boundary = cli_boundary
    run = boundary.run
    before = _paused_project(run.root, capsys)
    boundary.entries = (
        FleetEntry(
            1,
            run.root,
            run.pid,
            run.process_start,
            run.run_id,
            run.agent,
            run.started_at,
        ),
    )
    boundary.observation = RunObservation("active")
    if ambiguous:
        boundary.entries += (
            replace(boundary.entries[0], run_id="other", pid=run.pid + 1),
        )
    verifications: list[FleetRun] = []

    def verify(selected: FleetRun, registry: Any = None) -> Any:
        verifications.append(selected)
        return supervisor_settings(selected.root).runtime.paths

    monkeypatch.setattr("ovcaq.tui.app.verify_run", verify)
    _interactive_streams(monkeypatch)
    result = main(["--root", str(run.root), "resume"])
    state = json.loads(
        (run.root / "docs/dev/project-management/ovcaq/state.json").read_text()
    )
    if ambiguous:
        assert result != 0
        assert state == before
        assert boundary.launches == [] and boundary.attachments == []
        return
    assert result == 0
    assert state["control"]["pause_requested"] is False
    assert state["revision"] > before["revision"]
    assert verifications and all(selected == run for selected in verifications)
    assert boundary.launches == []
    assert len(boundary.attachments) == 1
    assert boundary.attachments[0]["run_id"] == run.run_id
    assert boundary.attachments[0]["root"] == run.root


def test_stale_resume_selection_fails_closed_without_launch_or_attach(
    cli_boundary: CliBoundary,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary = cli_boundary
    run = boundary.run
    before = _paused_project(run.root, capsys)
    boundary.entries = (
        FleetEntry(
            1,
            run.root,
            run.pid,
            run.process_start,
            run.run_id,
            run.agent,
            run.started_at,
        ),
    )
    boundary.observation = RunObservation("active")

    def stale(selected: FleetRun, registry: Any = None) -> Any:
        raise RuntimeError("selected run was replaced")

    monkeypatch.setattr("ovcaq.tui.app.verify_run", stale)
    _interactive_streams(monkeypatch)
    assert main(["--root", str(run.root), "resume"]) != 0
    assert (
        json.loads(
            (run.root / "docs/dev/project-management/ovcaq/state.json").read_text()
        )
        == before
    )
    assert boundary.launches == []
    assert boundary.attachments == []


def test_concurrent_resume_launch_loser_never_retries_or_attaches_other_owner(
    cli_boundary: CliBoundary,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary = cli_boundary
    root = boundary.run.root
    _paused_project(root, capsys)
    attempts: list[Path] = []
    evidence = LaunchFailureEvidence(
        1,
        "another supervisor owns the run lock",
        root / "docs/dev/project-management/ovcaq/launch-report",
    )

    def lose(selected: Path, **kwargs: Any) -> LaunchedSupervisor:
        attempts.append(selected)
        raise LaunchError(evidence)

    monkeypatch.setattr("ovcaq.cli.launch_supervisor", lose)
    _interactive_streams(monkeypatch)
    assert main(["--root", str(root), "resume"]) != 0
    assert attempts == [root]
    assert boundary.attachments == []
    captured = capsys.readouterr()
    assert evidence.detail in captured.err


def test_resume_honors_configured_agent_when_restarting_after_pause(
    cli_boundary: CliBoundary,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary = cli_boundary
    root = boundary.run.root
    (root / "ovcaq.toml").write_text(
        'agent = "generic"\n[agents.generic]\ncommand = ["python"]\n', encoding="utf-8"
    )
    boundary.run = replace(boundary.run, agent="generic")
    _paused_project(root, capsys)
    _interactive_streams(monkeypatch)
    assert main(["--root", str(root), "resume"]) == 0
    assert len(boundary.launches) == 1
    launched_root, agent_override = boundary.launches[0]
    assert launched_root == root
    assert agent_override in (None, "generic")
    assert len(boundary.attachments) == 1
    assert boundary.attachments[0]["run_id"] == boundary.run.run_id
