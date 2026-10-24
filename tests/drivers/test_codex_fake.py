"""Real subprocess evidence for the versioned fake Codex executable."""

import json
import os
import select
import signal
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ovcaq.config import AgentSettings
from ovcaq.drivers.base import LaunchRequest
from ovcaq.drivers.codex import CodexDriver
from ovcaq.events.model import FailureClass, ObservationType
from ovcaq.paths import state_path
from ovcaq.state.commands import StateService
from ovcaq.state.store import StateStore

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "codex" / "v1"
FAKE = FIXTURES / "fake_codex.py"


@pytest.fixture
def fake_environment(tmp_path: Path) -> dict[str, str]:
    environment = {"PATH": os.defpath, "OVCAQ_FAKE_MARKER": "temporary-test"}
    for key in ("HOME", "XDG_CONFIG_HOME", "XDG_STATE_HOME"):
        home = tmp_path / key.lower()
        home.mkdir()
        (home / "do-not-read").write_text("isolated sentinel")
        environment[key] = str(home)
    return environment


def driver(environment: dict[str, str], scenario: str = "healthy") -> CodexDriver:
    return CodexDriver(
        AgentSettings(
            name="codex",
            command=(sys.executable, str(FAKE)),
            tiers={"workhorse": "fixture-model"},
            environment=environment | {"OVCAQ_FAKE_SCENARIO": scenario},
            options={},
        ),
        run_id="fake-run",
    )


def request(tmp_path: Path, model=None, effort=None) -> LaunchRequest:
    return LaunchRequest(
        root=tmp_path,
        phase="build",
        prompt="--prompt 'literal'; $(no-shell)\nnext",
        model=model,
        effort=effort,
        timeout_seconds=10,
        session_dir=tmp_path / "session",
    )


def execute(adapter: CodexDriver, launch: LaunchRequest):
    spec = adapter.build_launch(launch)
    result = subprocess.run(
        spec.argv,
        cwd=spec.cwd,
        env=dict(spec.env),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    evidence, *lines = result.stdout.splitlines()
    return result, json.loads(evidence), lines


@pytest.mark.parametrize("model", [None, "workhorse", "fixture-model"])
@pytest.mark.parametrize("effort", [None, "low", "medium", "high", "xhigh"])
def test_exact_launch_contract(tmp_path, fake_environment, model, effort):
    adapter = driver(fake_environment)
    launch = request(tmp_path, model, effort)
    spec = adapter.build_launch(launch)
    expected = [
        "--ask-for-approval",
        "never",
        "exec",
        "--json",
        "--sandbox",
        "workspace-write",
        "-C",
        str(tmp_path),
    ]
    if model is not None:
        expected += ["-m", "fixture-model"]
    if effort is not None:
        expected += ["-c", f'model_reasoning_effort="{effort}"']
    expected += ["--", launch.prompt]
    assert spec.argv == (sys.executable, str(FAKE), *expected)
    assert spec.cwd == tmp_path
    assert spec.raw_format == "codex-exec-json-v1"
    result, evidence, _ = execute(adapter, launch)
    assert result.returncode == 0
    assert result.stderr == ""
    assert evidence == {
        "type": "fake_invocation",
        "argv": expected,
        "cwd": str(tmp_path),
        "stdin_closed": True,
        "environment": {
            key: spec.env[key]
            for key in (
                "HOME",
                "XDG_CONFIG_HOME",
                "XDG_STATE_HOME",
                "OVCAQ_FAKE_SCENARIO",
                "OVCAQ_FAKE_MARKER",
            )
        },
    }


@pytest.mark.parametrize(
    "arguments, text",
    [
        (["--version"], "codex-cli 0.160.0"),
        (["login", "status"], "Logged in with fixture authentication"),
    ],
)
def test_probe_invocation_evidence(tmp_path, fake_environment, arguments, text):
    result = subprocess.run(
        (sys.executable, str(FAKE), *arguments),
        cwd=tmp_path,
        env=fake_environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    (evidence,) = result.stderr.splitlines()
    (output,) = result.stdout.splitlines()
    assert result.returncode == 0
    assert output == text
    record = json.loads(evidence)
    assert record["argv"] == arguments
    assert record["cwd"] == str(tmp_path)
    assert record["stdin_closed"] is True


@pytest.mark.parametrize(
    "scenario, healthy, detail",
    [
        ("healthy", True, "authentication verified"),
        ("version-failed", False, "version check failed"),
        ("version-empty", False, "missing Codex version"),
        ("version-unsupported", False, "observed 0.159.0; pinned 0.160.0"),
        ("version-timeout", False, "version check timed out after 5 seconds"),
        ("auth-failed", False, "authentication check failed"),
        ("auth-timeout", False, "authentication check timed out after 5 seconds"),
    ],
)
def test_driver_probe_modes(fake_environment, scenario, healthy, detail):
    health = driver(fake_environment, scenario).probe()
    assert health.healthy is healthy
    assert detail in health.detail


@pytest.mark.parametrize(
    "scenario, exit_code",
    [
        ("healthy", 0),
        ("lanes", 0),
        ("malformed", 0),
        ("tool-active", 0),
        ("rate-limited", 1),
        ("authentication-failed", 1),
        ("connectivity-failed", 1),
        ("permission-failed", 1),
    ],
)
def test_fixture_replay(tmp_path, fake_environment, scenario, exit_code):
    adapter = driver(fake_environment, scenario)
    result, _, lines = execute(adapter, request(tmp_path))
    assert result.returncode == exit_code
    assert "\n".join(lines) + "\n" == (FIXTURES / f"{scenario}.jsonl").read_text()
    observations = [item for line in lines for item in adapter.decode(line)]
    assert observations
    if scenario == "malformed":
        assert any(item.type == ObservationType.RAW_UNKNOWN for item in observations)
    if scenario == "healthy":
        assert adapter.summarize(observations, result.returncode).success


@pytest.mark.parametrize(
    "scenario, failure, reset",
    [
        ("native-reset", FailureClass.RATE_LIMIT, True),
        ("native-no-reset", FailureClass.RATE_LIMIT, False),
        ("noisy-success", None, False),
    ],
)
def test_native_failure_and_noisy_success(
    tmp_path, fake_environment, scenario, failure, reset
):
    adapter = driver(fake_environment, scenario)
    before = datetime.now(UTC)
    result, _, lines = execute(adapter, request(tmp_path))
    observations = [item for line in lines for item in adapter.decode(line)]
    summary = adapter.summarize(observations, result.returncode)
    assert result.returncode == (0 if failure is None else 1)
    assert summary.success is (failure is None)
    assert summary.failure_class == failure
    assert summary.session_id == "fake-native"
    assert (summary.rate_limit_reset_at is not None) is reset
    if reset:
        assert before + timedelta(seconds=59) <= summary.rate_limit_reset_at
        assert summary.rate_limit_reset_at <= datetime.now(UTC) + timedelta(seconds=61)
    if failure is None:
        assert any(
            item.type == ObservationType.ACTIVITY_MESSAGE for item in observations
        )
        assert not any(
            item.type == ObservationType.RATE_LIMIT_STARTED for item in observations
        )


def test_fake_keeps_temporary_homes_untouched(tmp_path, fake_environment, monkeypatch):
    monkeypatch.setenv("HOST_ONLY_MARKER", "not-selected")
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    adapter = driver(fake_environment)
    assert adapter.probe().healthy
    result, evidence, _ = execute(adapter, request(tmp_path))
    assert "HOST_ONLY_MARKER" not in evidence["environment"]
    assert "not-selected" not in result.stdout
    assert {
        path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()
    } == before


def process_record(process):
    assert process.stdout is not None
    assert select.select([process.stdout], [], [], 5)[0], "fake evidence timed out"
    return json.loads(process.stdout.readline())


@pytest.mark.parametrize("scenario", ["descendant-term", "descendant-kill"])
def test_descendant_signal_modes(tmp_path, fake_environment, scenario):
    spec = driver(fake_environment, scenario).build_launch(request(tmp_path))
    process = subprocess.Popen(
        spec.argv,
        cwd=spec.cwd,
        env=dict(spec.env),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    child_pid = None
    try:
        assert process_record(process)["stdin_closed"] is True
        evidence = process_record(process)
        child_pid = evidence["pid"]
        assert evidence["pgid"] == process.pid
        assert evidence["parent_pid"] == process.pid
        assert os.getpgid(child_pid) == process.pid
        os.killpg(process.pid, signal.SIGTERM)
        if scenario == "descendant-kill":
            with pytest.raises(subprocess.TimeoutExpired):
                process.wait(timeout=0.2)
            assert os.getpgid(child_pid) == process.pid
            # Kill and reap the child first so group KILL cannot orphan it.
            os.kill(child_pid, signal.SIGKILL)
        reaped = process_record(process)
        expected = signal.SIGKILL if scenario == "descendant-kill" else signal.SIGTERM
        assert reaped == {"type": "fake_descendant_reaped", "returncode": -expected}
        with pytest.raises(ProcessLookupError):
            os.kill(child_pid, 0)
        child_pid = None
        if scenario == "descendant-kill":
            os.killpg(process.pid, signal.SIGKILL)
        assert process.wait(timeout=5) == (
            -signal.SIGKILL if scenario.endswith("kill") else 0
        )
    finally:
        if child_pid is not None:
            try:
                os.kill(child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
        process.communicate(timeout=5)


def installed_cli(root, environment, *arguments):
    executable = Path(sys.executable).with_name("ovcaq")
    assert executable.is_file(), "the test environment must install the ovcaq CLI"
    result = subprocess.run(
        [str(executable), "--root", str(root), "--json", *arguments],
        cwd=root,
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    return json.loads(result.stdout)


def assert_prd_completion(
    commands: list[dict],
    reads: list[dict],
    before: dict,
    phase: str,
    environment: dict[str, str],
    tmp_path: Path,
    prd: Path,
    historical: dict,
    current: dict,
) -> None:
    handoff_revision = before["revision"] + (1 if phase == "done" else 0)
    prd_completions = [
        record for record in commands if "complete-prd" in record["argv"]
    ]
    if phase == "done":
        assert len(prd_completions) == 1
        assert prd_completions[0]["argv"] == [
            environment["OVCAQ_FAKE_CLI"],
            "--root",
            str(tmp_path),
            "--json",
            "workflow",
            "complete-prd",
            "--prd",
            prd.name,
            "--expected-revision",
            str(before["revision"]),
        ]
        assert prd_completions[0]["result"]["revision"] == handoff_revision
        assert prd_completions[0]["result"]["result"] == current
        assert reads[-1]["result"]["batch"]["completed_prds"] == [historical, current]
        assert commands.index(prd_completions[0]) < commands.index(reads[-1])
    else:
        assert prd_completions == []


def assert_handoff_observation(
    records: list[dict], after: dict, phase: str, outcome: str, next_phase: str
) -> None:
    handoffs = [
        record for record in records if record["type"] == "fake_workflow_handoff"
    ]
    assert handoffs == [
        {
            "type": "fake_workflow_handoff",
            "phase": phase,
            "outcome": outcome,
            "revision": after["revision"],
            "result": {"phase": after["work"]["phase"], "next_phase": next_phase},
        }
    ]


def assert_workflow_handoff(
    commands,
    records,
    store,
    before,
    phase,
    outcome,
    next_phase,
    environment,
    tmp_path,
    prd,
    historical,
    current,
):
    completions = [record for record in commands if "phase-complete" in record["argv"]]
    assert len(completions) == 1
    assert commands[-1] == completions[0]
    reads = [record for record in commands if record["argv"][-2:] == ["state", "show"]]
    assert len(reads) == (2 if phase in {"build", "done"} else 1)
    handoff_revision = before["revision"] + (1 if phase == "done" else 0)
    assert reads[-1]["result"]["revision"] == handoff_revision
    assert_prd_completion(
        commands, reads, before, phase, environment, tmp_path, prd, historical, current
    )
    assert completions[0]["argv"] == [
        environment["OVCAQ_FAKE_CLI"],
        "--root",
        str(tmp_path),
        "--json",
        "workflow",
        "phase-complete",
        "--outcome",
        outcome,
        "--expected-revision",
        str(handoff_revision),
    ]
    after = store.read()
    assert after["revision"] == before["revision"] + (2 if phase == "done" else 1)
    assert after["batch"]["completed_prds"] == (
        [historical, current] if phase == "done" else [historical]
    )
    assert after["work"]["next_phase"] == next_phase
    assert_handoff_observation(records, after, phase, outcome, next_phase)


def prepare_workflow_handoff(
    tmp_path: Path, fake_environment: dict[str, str]
) -> tuple[Path, dict[str, str], CodexDriver, StateStore, dict, dict]:
    installed_cli(tmp_path, fake_environment, "init")
    backlog = tmp_path / "docs/dev/project-management/prds/backlog"
    backlog.mkdir(parents=True)
    prd = backlog / "00001-fixture.md"
    prd.write_text("# Fixture PRD\n")
    installed_cli(
        tmp_path,
        fake_environment,
        "state",
        "set",
        "work.prd",
        json.dumps(prd.name),
        "--unsafe",
    )
    environment = fake_environment | {
        "OVCAQ_FAKE_CLI": str(Path(sys.executable).with_name("ovcaq"))
    }
    adapter = driver(environment, "workflow")
    store = StateStore(state_path(tmp_path))
    StateService(store).start_batch("fake-workflow", "2026-10-25T00:00:00Z")
    historical = {
        "filename": "00000-prior.md",
        "cycles": 2,
        "autonomous_decisions": 1,
        "escalated_decisions": 0,
        "tasks_completed": 3,
        "tasks_total": 3,
    }
    store.transaction(lambda state: state["batch"]["completed_prds"].append(historical))
    current = {
        "filename": prd.name,
        "cycles": 1,
        "autonomous_decisions": 0,
        "escalated_decisions": 0,
        "tasks_completed": 0,
        "tasks_total": 0,
    }
    return prd, environment, adapter, store, historical, current


def test_command_backed_workflow_handoffs(tmp_path, fake_environment):
    prd, environment, adapter, store, historical, current = prepare_workflow_handoff(
        tmp_path, fake_environment
    )
    all_commands = []
    for phase, outcome, next_phase in [
        ("build", "tasks_done", "review"),
        ("review", "converged", "done"),
        ("done", "drained", ""),
    ]:
        before = store.read()
        assert before["work"]["phase"] == phase
        assert before["batch"]["completed_prds"] == [historical]
        result, invocation, lines = execute(adapter, request(tmp_path))
        assert result.returncode == 0
        assert invocation["cwd"] == str(tmp_path)
        records = [json.loads(line) for line in lines]
        commands = [
            record for record in records if record["type"] == "fake_workflow_command"
        ]
        all_commands.extend(commands)
        assert_workflow_handoff(
            commands,
            records,
            store,
            before,
            phase,
            outcome,
            next_phase,
            environment,
            tmp_path,
            prd,
            historical,
            current,
        )
        observations = [item for line in lines for item in adapter.decode(line)]
        assert adapter.summarize(observations, result.returncode).success
    selections = [record for record in all_commands if "select" in record["argv"]]
    assert len(selections) == 1
    assert selections[0]["result"]["prd"] == prd.name
    assert store.read()["batch"]["completed_prds"] == [historical, current]
    assert store.read()["work"]["completed_phases"] == ["review"]
