from __future__ import annotations

import json
import os
import select
import signal
import stat
import subprocess
import sys
import time
import unicodedata
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from ovcaq.cli import main
from ovcaq.config import supervisor_settings
from ovcaq.paths import ensure_runtime_layout
from ovcaq.runtime.registry import (
    FleetRegistry,
    FleetRun,
    ProcessIdentity,
    process_matches,
)
from ovcaq.state.commands import StateService
from ovcaq.state.schema import new_state
from ovcaq.state.store import StateStore
from ovcaq.supervisor_cli import LaunchedSupervisor, LaunchError, launch_supervisor

STAMP = "2026-10-03T12:00:00Z"
SECRET_PREFIX = "sk-proj"
SECRET = f"{SECRET_PREFIX}-synthetic-launcher-credential-12345678901234567890"
DEFAULT_RUNTIME = Path("docs/dev/project-management/ovcaq")


@pytest.fixture(autouse=True)
def isolated_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("HOME", "XDG_STATE_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
        directory = tmp_path / key.lower()
        directory.mkdir()
        monkeypatch.setenv(key, str(directory))
    monkeypatch.delenv("OVCAQ_LAUNCH_REPORT", raising=False)
    monkeypatch.setenv(
        "PYTHONPATH", os.pathsep.join(os.path.abspath(part) for part in sys.path)
    )


def project(tmp_path: Path, layout: str = "default") -> Path:
    root = tmp_path / "project"
    root.mkdir()
    configuration = (
        'agent = "claude"\n[agents.claude]\n'
        f"command = {json.dumps([sys.executable, '-c', 'raise SystemExit(91)'])}\n"
        'tiers = { sonnet = "model-s", opus = "model-o" }\n'
        '[agents.claude.options]\npermission_mode = "auto"\n'
    )
    if layout == "contained":
        configuration += '[workflow]\nruntime_root = "private/runtime"\n'
    elif layout == "external":
        configuration += (
            "[runtime]\nexternal_state_root = "
            + json.dumps(str(tmp_path / "external-runtime"))
            + "\n"
        )
    (root / "ovcaq.toml").write_text(configuration, encoding="utf-8")
    paths = ensure_runtime_layout(supervisor_settings(root).runtime.paths)
    StateStore(paths.state_file).initialize(new_state(repo_root=root))
    service(root).start_batch("launcher-outcomes", STAMP)
    StateStore(paths.state_file).transaction(
        lambda state: state["work"].update(phase="done", next_phase="")
    )
    return root


def service(root: Path) -> StateService:
    return StateService(StateStore(supervisor_settings(root).runtime.paths.state_file))


def finish(worker: subprocess.Popen[Any]) -> None:
    if worker.poll() is None:
        try:
            os.killpg(worker.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    worker.wait(timeout=5)
    for stream in (worker.stdin, worker.stdout, worker.stderr):
        if stream is not None:
            stream.close()


def line(worker: subprocess.Popen[Any]) -> str:
    assert worker.stdout is not None
    deadline = time.monotonic() + 5
    received = bytearray()
    while not received.endswith(b"\n"):
        remaining = deadline - time.monotonic()
        assert remaining > 0, "child missed its process barrier"
        ready, _, _ = select.select([worker.stdout], [], [], remaining)
        assert ready, "child missed its process barrier"
        part = os.read(worker.stdout.fileno(), 1)
        assert part, f"child exited before its barrier: {worker.poll()}"
        received.extend(part)
    return received.decode().strip()


@dataclass
class SpawnBoundary:
    original: Any
    children: list[subprocess.Popen[Any]] = field(default_factory=list)
    reports: list[Path] = field(default_factory=list)
    preserved: list[bytes] = field(default_factory=list)
    before: Callable[[], None] = lambda: None
    after_exit: Callable[[], None] = lambda: None
    after_publication: Callable[[subprocess.Popen[Any]], None] = lambda worker: None
    publication: str = "published"
    replacement: str | None = None
    wait_before_return: bool = True

    def spawn(self, argv: Any, **options: Any) -> subprocess.Popen[Any]:
        if "--no-tui" not in argv or "run" not in argv:
            return self.original(argv, **options)
        report = Path(options["env"]["OVCAQ_LAUNCH_REPORT"])
        assert stat.S_IMODE(report.stat().st_mode) == 0o600
        assert report.is_file() and not report.is_symlink()
        self.reports.append(report)
        self.before()
        if self.replacement is not None:
            argv = [sys.executable, "-c", self.replacement, *argv[1:]]
        if not self.wait_before_return:
            options.update(stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        worker = self.original(argv, **options)
        self.children.append(worker)
        if self.wait_before_return:
            worker.wait(timeout=10)
            self.preserved.append(report.read_bytes())
            self.after_exit()
        else:
            assert line(worker) == self.publication
            self.after_publication(worker)
        return worker


@pytest.fixture
def boundary(monkeypatch: pytest.MonkeyPatch) -> Iterator[SpawnBoundary]:
    target = SpawnBoundary(subprocess.Popen)
    monkeypatch.setattr("ovcaq.supervisor_cli.subprocess.Popen", target.spawn)
    try:
        yield target
    finally:
        for worker in target.children:
            finish(worker)


def assert_drained(root: Path, boundary: SpawnBoundary) -> None:
    assert len(boundary.children) == 1
    assert boundary.children[0].returncode == 0
    assert service(root).show()["batch"]["status"] == "completed"
    registry = FleetRegistry(supervisor_settings(root).runtime.paths.fleet_root)
    assert registry.snapshot().live == ()


def test_real_empty_child_commits_completion_before_parent_first_poll(
    tmp_path: Path, boundary: SpawnBoundary
) -> None:
    root = project(tmp_path)
    marker = tmp_path / "custom-launcher.json"
    wrapper = (
        "import json, runpy, sys; from pathlib import Path; "
        f"Path({str(marker)!r}).write_text(json.dumps(sys.argv[1:])); "
        "runpy.run_module('ovcaq', run_name='__main__')"
    )
    try:
        launched = launch_supervisor(
            root,
            agent=None,
            timeout_seconds=2,
            argv_prefix=(sys.executable, "-c", wrapper),
        )
    finally:
        assert_drained(root, boundary)
    assert isinstance(launched, LaunchedSupervisor)
    assert launched.run is None
    assert json.loads(marker.read_text()) == ["--root", str(root), "run", "--no-tui"]
    assert not boundary.reports[0].exists()


@pytest.mark.parametrize("command", ["run", "resume"])
def test_interactive_quick_completion_returns_zero_without_live_attachment(
    tmp_path: Path,
    boundary: SpawnBoundary,
    monkeypatch: pytest.MonkeyPatch,
    command: str,
) -> None:
    root = project(tmp_path)
    if command == "resume":
        service(root).request_pause(None)
    monkeypatch.setattr("ovcaq.cli.sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("ovcaq.cli.sys.stdout.isatty", lambda: True)

    def unexpected_attachment(**kwargs: Any) -> Any:
        pytest.fail("completed child has no live run to attach")

    monkeypatch.setattr("ovcaq.tui.app.attach", unexpected_attachment)
    assert main(["--root", str(root), command]) == 0
    assert_drained(root, boundary)
    assert service(root).show()["control"]["pause_requested"] is False


@pytest.mark.parametrize("layout", ["contained", "external"])
def test_configured_layout_drains_without_creating_unused_default_tree(
    tmp_path: Path, boundary: SpawnBoundary, layout: str
) -> None:
    root = project(tmp_path, layout)
    assert not (root / DEFAULT_RUNTIME).exists()
    try:
        launched = launch_supervisor(root, agent=None, timeout_seconds=2)
    finally:
        assert not (root / DEFAULT_RUNTIME).exists()
    assert launched.run is None
    assert_drained(root, boundary)
    paths = supervisor_settings(root).runtime.paths
    assert paths.state_file.exists()
    assert boundary.reports[0].is_relative_to(paths.runtime_root)
    assert not (root / DEFAULT_RUNTIME).exists()


@pytest.mark.parametrize("exit_code", [0, 23])
@pytest.mark.parametrize("previous_completion", [False, True])
def test_exit_without_exact_child_commit_proof_is_failure(
    tmp_path: Path,
    boundary: SpawnBoundary,
    exit_code: int,
    previous_completion: bool,
) -> None:
    root = project(tmp_path)
    if previous_completion:
        service(root).skip_empty_drain_capabilities(completed_at=STAMP)
    before = service(root).show()
    boundary.replacement = f"raise SystemExit({exit_code})"
    with pytest.raises(LaunchError) as caught:
        launch_supervisor(root, agent=None, timeout_seconds=2)
    assert caught.value.evidence.exit_code == exit_code
    assert caught.value.evidence.path == boundary.reports[0]
    assert caught.value.evidence.detail
    assert service(root).show() == before
    assert len(boundary.children) == 1


def test_child_completion_report_cannot_complete_a_replacement_batch(
    tmp_path: Path, boundary: SpawnBoundary
) -> None:
    root = project(tmp_path)
    replacement: list[dict[str, Any]] = []

    def replace_completed_batch() -> None:
        assert boundary.children[0].returncode == 0
        assert service(root).show()["batch"]["status"] == "completed"
        service(root).start_batch("replacement-batch", "2026-10-03T12:00:02Z")
        replacement.append(service(root).show())

    boundary.after_exit = replace_completed_batch
    with pytest.raises(LaunchError) as caught:
        launch_supervisor(root, agent=None, timeout_seconds=2)
    assert caught.value.evidence.exit_code == 0
    assert caught.value.evidence.path == boundary.reports[0]
    assert caught.value.evidence.detail
    assert len(boundary.children) == 1
    assert service(root).show() == replacement[0]
    assert boundary.reports[0].read_bytes() == boundary.preserved[0]


def assert_private_diagnostic(boundary: SpawnBoundary, error: LaunchError) -> str:
    assert len(boundary.children) == 1
    assert boundary.children[0].returncode not in (None, 0)
    evidence = error.evidence
    assert evidence.exit_code == boundary.children[0].returncode
    assert evidence.path == boundary.reports[0]
    raw = boundary.preserved[0]
    assert 0 < len(raw) <= 4096
    preserved = raw.decode("utf-8")
    for text in (preserved, evidence.detail):
        assert 0 < len(text.encode("utf-8")) <= 4096
        assert "\x1b" not in text and "\x00" not in text
        assert SECRET not in text
        assert any(
            word in text.lower()
            for word in ("config", "runtime", "directory", "session")
        )
    assert stat.S_IMODE(evidence.path.stat().st_mode) == 0o600
    assert evidence.path.read_bytes() == raw
    return preserved


def test_child_configuration_failure_preserves_actionable_private_report(
    tmp_path: Path, boundary: SpawnBoundary
) -> None:
    root = project(tmp_path)
    config = root / "ovcaq.toml"
    original = config.read_text()
    invalid = "\x1b[31m" + SECRET + "\x00" + "é" * 5000
    boundary.before = lambda: config.write_text(
        original + "[runtime]\nmin_free_bytes = " + json.dumps(invalid) + "\n"
    )
    with pytest.raises(LaunchError) as caught:
        launch_supervisor(root, agent=None, timeout_seconds=2)
    preserved = assert_private_diagnostic(boundary, caught.value)
    assert "min_free_bytes" in preserved
    assert "min_free_bytes" in caught.value.evidence.detail


@pytest.mark.parametrize("collision", ["file", "symlink"])
def test_early_layout_failure_preserves_diagnostic_and_collision(
    tmp_path: Path, boundary: SpawnBoundary, collision: str
) -> None:
    root = project(tmp_path)
    sessions = supervisor_settings(root).runtime.paths.sessions
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "preserve"
    sentinel.write_bytes(b"untouched")

    def collide() -> None:
        if sessions.exists():
            sessions.rmdir()
        if collision == "file":
            sessions.write_bytes(b"occupied")
        else:
            sessions.symlink_to(outside, target_is_directory=True)

    boundary.before = collide
    with pytest.raises(LaunchError) as caught:
        launch_supervisor(root, agent=None, timeout_seconds=2)
    assert_private_diagnostic(boundary, caught.value)
    assert sentinel.read_bytes() == b"untouched"
    assert sorted(path.name for path in outside.iterdir()) == ["preserve"]
    if collision == "file":
        assert sessions.read_bytes() == b"occupied"
    else:
        assert sessions.is_symlink() and sessions.resolve() == outside


@pytest.mark.parametrize(
    "destination", ["outside", "symlink", "traversal", "directory"]
)
def test_child_rejects_unsafe_report_destination_without_overwriting_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, destination: str
) -> None:
    root = project(tmp_path)
    runtime = supervisor_settings(root).runtime.paths.runtime_root
    outside = root / "outside.txt"
    outside.write_text("preserve me")
    report = outside
    if destination == "symlink":
        report = runtime / "launch-report"
        report.symlink_to(outside)
    elif destination == "traversal":
        report = runtime / "../../../outside.txt"
    elif destination == "directory":
        report = runtime / "launch-report"
        report.mkdir()
    monkeypatch.setenv("OVCAQ_LAUNCH_REPORT", str(report))
    before = service(root).show()
    assert main(["--root", str(root), "run", "--no-tui"]) != 0
    assert outside.read_text() == "preserve me"
    assert service(root).show() == before
    if destination == "directory":
        assert report.is_dir() and list(report.iterdir()) == []
    elif destination == "symlink":
        assert report.is_symlink()


def test_report_environment_is_consumed_on_driver_construction_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = project(tmp_path)
    report = supervisor_settings(root).runtime.paths.runtime_root / "launch-report"
    report.touch(mode=0o600)
    monkeypatch.setenv("OVCAQ_LAUNCH_REPORT", str(report))
    arguments = ["--root", str(root), "run", "--no-tui", "--agent", "absent-agent"]
    assert main(arguments) != 0
    assert "OVCAQ_LAUNCH_REPORT" not in os.environ
    assert report.stat().st_mode & 0o777 == 0o600
    assert b"absent-agent" in report.read_bytes()


def test_reflected_hostile_agent_preserves_bounded_private_diagnostics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = project(tmp_path)
    report = supervisor_settings(root).runtime.paths.runtime_root / "launch-report"
    report.touch(mode=0o600)
    monkeypatch.setenv("OVCAQ_LAUNCH_REPORT", str(report))
    marker = "hostile-agent-"
    hostile = marker + "\x1b[31m" + SECRET + "\x00\x07\x9b" + "é" * 5000
    arguments = ["--root", str(root), "run", "--no-tui", "--agent", hostile]
    capsys.readouterr()
    assert main(arguments) != 0
    detail = capsys.readouterr().err
    assert "OVCAQ_LAUNCH_REPORT" not in os.environ
    assert report.is_file() and not report.is_symlink()
    assert stat.S_IMODE(report.stat().st_mode) == 0o600
    raw = report.read_bytes()
    assert 0 < len(raw) <= 4096
    for text in (raw.decode("utf-8"), detail):
        assert 0 < len(text.encode("utf-8")) <= 4096
        assert marker in text
        assert SECRET not in text
        assert all(
            unicodedata.category(character) != "Cc" or character == "\n"
            for character in text
        )


OWNER = """
import os, sys
from pathlib import Path
from ovcaq.config import supervisor_settings
from ovcaq.runtime.registry import FleetEntry, FleetRegistry, RunLock, process_identity
from ovcaq.runtime.session import (
    SessionMetadata, publish_run_metadata, cleanup_run_records,
)
from ovcaq.runtime._run_observation import publish_terminal_evidence
from ovcaq.state.commands import StateService
from ovcaq.state.store import StateStore
root = Path(sys.argv[sys.argv.index('--root') + 1])
paths = supervisor_settings(root).runtime.paths
identity = process_identity(os.getpid())
lock = RunLock.acquire(paths.run_lock)
agent = sys.argv[sys.argv.index('--agent') + 1] if '--agent' in sys.argv else 'generic'
entry = FleetEntry(1, root, identity.pid, identity.started, 'selected-child',
                   agent, '2026-10-03T12:00:00Z')
metadata = SessionMetadata(1, entry.run_id, 'supervisor', entry.agent, entry.pid,
                           entry.process_start, entry.started_at)
registry = FleetRegistry(paths.fleet_root)
registry.publish(entry)
publish_run_metadata(paths, metadata)
print('published', flush=True)
command = sys.stdin.readline().strip()
service = StateService(StateStore(paths.state_file))
if command != 'fail':
    service.skip_empty_drain_capabilities(completed_at='2026-10-03T12:00:01Z')
proof_run_id = 'unrelated-child' if command == 'unrelated-proof' else entry.run_id
publish_terminal_evidence(
    paths, run_id=proof_run_id, process=identity, state=service.show(),
)
cleanup_run_records(paths, metadata, entry)
registry.remove(entry.run_id, expected=entry)
lock.close()
raise SystemExit(23 if command == 'fail' else 0)
"""


def release(boundary: SpawnBoundary, command: str = "complete") -> None:
    worker = boundary.children[0]
    assert worker.stdin is not None
    worker.stdin.write((command + "\n").encode())
    worker.stdin.flush()
    assert worker.wait(timeout=5) == (23 if command == "fail" else 0)


@pytest.mark.parametrize("agent", [None, "alternate"])
def test_live_handshake_returns_exact_published_child_identity(
    tmp_path: Path, boundary: SpawnBoundary, agent: str | None
) -> None:
    root = project(tmp_path)
    config = root / "ovcaq.toml"
    config.write_text(
        config.read_text() + "[agents.alternate]\n"
        f"command = {json.dumps([sys.executable, '-c', 'raise SystemExit(92)'])}\n"
        'tiers = { sonnet = "model-s", opus = "model-o" }\n'
    )
    boundary.replacement, boundary.wait_before_return = OWNER, False
    launched = launch_supervisor(root, agent=agent, timeout_seconds=2)
    registry = FleetRegistry(supervisor_settings(root).runtime.paths.fleet_root)
    entries = registry.snapshot().live
    assert len(entries) == 1
    assert launched.run == FleetRun.from_entry(entries[0])
    assert launched.run.pid == boundary.children[0].pid
    assert launched.run.agent == (agent or "generic")
    assert boundary.children[0].poll() is None
    assert len(boundary.children) == 1
    assert not boundary.reports[0].exists()
    release(boundary)


def delay_publication(boundary: SpawnBoundary) -> None:
    boundary.replacement = (
        "import sys\nprint('waiting', flush=True)\nsys.stdin.readline()\n" + OWNER
    )
    boundary.wait_before_return = False
    boundary.publication = "waiting"


def test_live_handshake_waits_for_publication_within_configured_deadline(
    tmp_path: Path, boundary: SpawnBoundary, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = project(tmp_path)
    delay_publication(boundary)
    polls: list[int | None] = []

    def release_after_first_poll(worker: subprocess.Popen[Any]) -> None:
        poll = worker.poll

        def polled() -> int | None:
            result = poll()
            polls.append(result)
            if len(polls) == 2:
                assert worker.stdin is not None
                worker.stdin.write(b"publish\n")
                worker.stdin.flush()
                assert line(worker) == "published"
            return result

        monkeypatch.setattr(worker, "poll", polled)

    boundary.after_publication = release_after_first_poll
    launched = launch_supervisor(root, agent=None, timeout_seconds=2)
    paths = supervisor_settings(root).runtime.paths
    entries = FleetRegistry(paths.fleet_root).snapshot()
    assert polls[:2] == [None, None]
    assert len(entries.live) == 1
    assert launched.run == FleetRun.from_entry(entries.live[0])
    assert launched.run.pid == boundary.children[0].pid
    assert len(boundary.children) == 1
    assert not boundary.reports[0].exists()
    release(boundary)


def test_unpublished_child_fails_within_configured_deadline(
    tmp_path: Path, boundary: SpawnBoundary
) -> None:
    root = project(tmp_path)
    before = service(root).show()
    delay_publication(boundary)
    started = time.monotonic()
    with pytest.raises(LaunchError) as caught:
        launch_supervisor(root, agent=None, timeout_seconds=0.15)
    assert 0.15 <= time.monotonic() - started < 2
    assert len(boundary.children) == 1
    assert boundary.children[0].poll() is None
    assert caught.value.evidence.exit_code is None
    assert caught.value.evidence.path == boundary.reports[0]
    assert boundary.reports[0].is_file()
    assert service(root).show() == before


@pytest.mark.parametrize(
    "outcome", ["complete", "fail", "replacement", "viewer-error", "unrelated-proof"]
)
def test_attachment_cleanup_race_requires_exact_successful_terminal_evidence(
    tmp_path: Path,
    boundary: SpawnBoundary,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    outcome: str,
) -> None:
    from ovcaq.tui.app import attach

    root = project(tmp_path)
    boundary.replacement, boundary.wait_before_return = OWNER, False
    monkeypatch.setattr("ovcaq.cli.sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("ovcaq.cli.sys.stdout.isatty", lambda: True)
    selections: list[str] = []

    def raced_attach(**kwargs: Any) -> Any:
        selections.append(kwargs["run_id"])
        command = outcome if outcome in ("fail", "unrelated-proof") else "complete"
        release(boundary, command)
        if outcome == "replacement":
            service(root).start_batch("replacement-batch", "2026-10-03T12:00:02Z")
        if outcome == "viewer-error":
            raise ValueError("unrelated viewer failure")
        return attach(**kwargs)

    monkeypatch.setattr("ovcaq.tui.app.attach", raced_attach)
    capsys.readouterr()
    code = main(["--root", str(root), "run"])
    captured = capsys.readouterr()
    assert (code == 0) is (outcome == "complete")
    assert selections == ["selected-child"]
    assert len(boundary.children) == 1
    assert "Traceback" not in captured.err
    if outcome == "complete":
        assert "no match" not in captured.err.lower()
        assert service(root).show()["batch"]["status"] == "completed"


@pytest.fixture(params=["exited", "starting"])
def duplicate_startup(request: pytest.FixtureRequest, boundary: SpawnBoundary) -> None:
    def assert_starting(worker: subprocess.Popen[Any]) -> None:
        assert worker.poll() is None

    if request.param == "starting":
        boundary.replacement = (
            "import runpy, select, sys\n"
            "print('starting', flush=True)\n"
            "if not select.select([sys.stdin], [], [], 10)[0]:\n"
            "    raise SystemExit(93)\n"
            "if sys.stdin.readline().strip() != 'continue':\n"
            "    raise SystemExit(94)\n"
            "runpy.run_module('ovcaq', run_name='__main__')\n"
        )
        boundary.wait_before_return = False
        boundary.publication = "starting"
        boundary.after_publication = assert_starting


def test_duplicate_owner_guides_attach_without_signaling_healthy_owner(
    tmp_path: Path,
    boundary: SpawnBoundary,
    monkeypatch: pytest.MonkeyPatch,
    duplicate_startup: None,
) -> None:
    root = project(tmp_path)
    environment = os.environ.copy()
    owner = boundary.original(
        [sys.executable, "-c", OWNER, "--root", str(root)],
        env=environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    sent: list[tuple[int, int]] = []
    original_kill = os.kill
    original_killpg = os.killpg

    def record_signal(pid: int, number: int) -> None:
        sent.append((pid, number))
        original_kill(pid, number)

    def record_group(pid: int, number: int) -> None:
        sent.append((pid, number))
        original_killpg(pid, number)

    monkeypatch.setattr("os.kill", record_signal)
    monkeypatch.setattr("os.killpg", record_group)
    try:
        assert line(owner) == "published"
        paths = supervisor_settings(root).runtime.paths
        entry = FleetRegistry(paths.fleet_root).snapshot().live[0]
        before = service(root).show()
        with pytest.raises(LaunchError) as caught:
            launch_supervisor(root, agent=None, timeout_seconds=2)
        detail = caught.value.evidence.detail
        assert "ovcaq attach" in detail
        assert "ovcaq stop" not in detail
        assert owner.poll() is None
        assert process_matches(ProcessIdentity(entry.pid, entry.process_start))
        assert FleetRegistry(paths.fleet_root).snapshot().live == (entry,)
        assert service(root).show() == before
        assert len(boundary.children) == 1
        assert not any(pid == owner.pid and number for pid, number in sent)
    finally:
        finish(owner)
