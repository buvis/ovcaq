from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class InstalledWheel:
    root: Path
    console_script: Path
    python: Path
    environment: dict[str, str]


@dataclass(frozen=True)
class InstalledPayloads:
    task: Path
    attempt_one: Path
    attempt_two: Path
    body: Path
    meta: Path
    contract: Path


def _command_text(command: list[str | Path]) -> str:
    return shlex.join(str(part) for part in command)


def _build_wheel(root: Path) -> Path:
    distribution = root / "dist"
    distribution.mkdir()
    build = subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(distribution)],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert build.returncode == 0, (
        f"wheel build failed ({build.returncode})\n"
        f"stdout:\n{build.stdout}\nstderr:\n{build.stderr}"
    )
    wheels = tuple(distribution.glob("*.whl"))
    assert len(wheels) == 1, f"wheel build produced unexpected artifacts: {wheels!r}"
    return wheels[0]


def _create_installed_environment(root: Path, wheel: Path) -> InstalledWheel:
    environment_root = root / "venv"
    create = subprocess.run(
        ["uv", "venv", "--python", sys.executable, str(environment_root)],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert create.returncode == 0, (
        f"venv creation failed ({create.returncode})\n"
        f"stdout:\n{create.stdout}\nstderr:\n{create.stderr}"
    )
    python = environment_root / "bin" / "python"
    install = subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--no-deps",
            "--python",
            str(python),
            str(wheel),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert install.returncode == 0, (
        f"wheel install failed ({install.returncode})\n"
        f"stdout:\n{install.stdout}\nstderr:\n{install.stderr}"
    )

    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PATH"] = os.pathsep.join(
        (str(environment_root / "bin"), environment.get("PATH", ""))
    )
    return InstalledWheel(
        root=environment_root,
        console_script=environment_root / "bin" / "ovcaq",
        python=python,
        environment=environment,
    )


@pytest.fixture(scope="session")
def installed_wheel(tmp_path_factory: pytest.TempPathFactory) -> InstalledWheel:
    root = tmp_path_factory.mktemp("installed-state-wheel")
    return _create_installed_environment(root, _build_wheel(root))


def _run(
    command: list[str | Path],
    *,
    cwd: Path,
    installed_wheel: InstalledWheel,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [str(part) for part in command],
        cwd=cwd,
        env=installed_wheel.environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"installed command failed ({result.returncode}): {_command_text(command)}\n"
        f"cwd: {cwd}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "Traceback" not in result.stderr
    return result


def _hostile_cwd(tmp_path: Path) -> Path:
    cwd = tmp_path / "arbitrary-cwd"
    decoy = cwd / "cli"
    decoy.mkdir(parents=True)
    (decoy / "__init__.py").write_text(
        "raise RuntimeError('checkout-relative cli import reached decoy')\n",
        encoding="utf-8",
    )
    return cwd


def test_installed_state_exports_service_with_functional_restore(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
) -> None:
    cwd = _hostile_cwd(tmp_path)
    root = tmp_path / "installed-state-service"
    root.mkdir()
    script = """
import json
import sys
from pathlib import Path

from ovcaq.state import StateService
from ovcaq.state.schema import new_state
from ovcaq.state.store import StateStore

root = Path(sys.argv[1])
store = StateStore(root / "state.json")
store.initialize(new_state(repo_root=root))

def mutate(state):
    state["work"]["prd"] = "current.md"

store.transaction(mutate)
result = StateService(store).restore(expected_revision=1)
print(json.dumps({"result": result, "state": store.read()}, sort_keys=True))
"""

    completed = _run(
        [installed_wheel.python, "-c", script, root],
        cwd=cwd,
        installed_wheel=installed_wheel,
    )

    payload = json.loads(completed.stdout)
    assert payload["result"] == {"revision": 2, "task_id": None}
    assert payload["state"]["revision"] == 2
    assert payload["state"]["work"]["prd"] is None


def test_installed_cli_normalizes_oversized_durable_integer(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
) -> None:
    cwd = _hostile_cwd(tmp_path)
    root = tmp_path / "installed-integer-limit"
    root.mkdir()
    _run(
        [installed_wheel.console_script, "--root", root, "--json", "init"],
        cwd=cwd,
        installed_wheel=installed_wheel,
    )
    state_path = root / "docs" / "dev" / "project-management" / "ovcaq" / "state.json"
    encoded = state_path.read_bytes()
    oversized = encoded.replace(
        b'"revision": 0,',
        b'"revision": ' + b"9" * 5_000 + b",",
        1,
    )
    assert oversized != encoded
    state_path.write_bytes(oversized)

    completed = subprocess.run(
        [
            installed_wheel.console_script,
            "--root",
            root,
            "--json",
            "state",
            "show",
        ],
        cwd=cwd,
        env=installed_wheel.environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert completed.returncode == 11
    assert completed.stdout == ""
    assert "Traceback" not in completed.stderr
    failure = json.loads(completed.stderr)
    assert failure["error"]["code"] == "resource_limit"
    assert state_path.read_bytes() == oversized


def _run_json_mutation(
    entrypoint: list[str | Path],
    root: Path,
    arguments: list[str | Path],
    *,
    cwd: Path,
    installed_wheel: InstalledWheel,
    revision: int,
    result_value: int | None,
) -> dict[str, object]:
    command = [
        *entrypoint,
        "--root",
        root,
        "--json",
        *arguments,
    ]
    completed = _run(command, cwd=cwd, installed_wheel=installed_wheel)
    payload = json.loads(completed.stdout)
    assert payload == {"ok": True, "revision": revision, "result": result_value}
    assert completed.stderr == ""
    return payload


def _attempt(number: int) -> dict[str, object]:
    return {
        "number": number,
        "tier": "full",
        "driver": "codex",
        "outcome": "completed",
        "review_cycle": None,
        "cause": None,
        "pipeline": "lean",
        "cleanup_outcome": None,
        "started_at": "2026-08-26T10:00:00Z",
        "finished_at": "2026-08-26T10:01:00Z",
        "commit_sha": None,
        "escalation": None,
        "metadata": {},
    }


def _assert_installed_reads(
    console: list[Path],
    module: list[str | Path],
    root: Path,
    cwd: Path,
    installed_wheel: InstalledWheel,
) -> None:
    help_result = _run(
        [*console, "state", "--help"],
        cwd=cwd,
        installed_wheel=installed_wheel,
    )
    assert help_result.stdout.startswith("usage: ovcaq state")
    assert help_result.stderr == ""

    _run_json_mutation(
        console,
        root,
        ["init"],
        cwd=cwd,
        installed_wheel=installed_wheel,
        revision=0,
        result_value=None,
    )

    show = _run(
        [*module, "--root", root, "state", "show"],
        cwd=cwd,
        installed_wheel=installed_wheel,
    )
    shown_state = json.loads(show.stdout)
    assert shown_state["revision"] == 0
    assert shown_state["work"]["repo_root"] == str(root)
    assert show.stderr == ""

    validate = _run(
        [*console, "--root", root, "state", "validate"],
        cwd=cwd,
        installed_wheel=installed_wheel,
    )
    assert json.loads(validate.stdout) == shown_state
    assert validate.stderr == ""

    get = _run(
        [*module, "--root", root, "state", "get", "work.repo_root"],
        cwd=cwd,
        installed_wheel=installed_wheel,
    )
    assert json.loads(get.stdout) == str(root)
    assert get.stderr == ""


def _write_installed_payloads(tmp_path: Path) -> InstalledPayloads:
    payloads = InstalledPayloads(
        task=tmp_path / "task.json",
        attempt_one=tmp_path / "attempt-one.json",
        attempt_two=tmp_path / "attempt-two.json",
        body=tmp_path / "body.md",
        meta=tmp_path / "meta.json",
        contract=tmp_path / "contract.md",
    )
    payloads.task.write_text(
        json.dumps({"name": "Installed CLI task"}), encoding="utf-8"
    )
    payloads.attempt_one.write_text(json.dumps(_attempt(1)), encoding="utf-8")
    payloads.attempt_two.write_text(json.dumps(_attempt(2)), encoding="utf-8")
    payloads.body.write_text("Body loaded from a file\n", encoding="utf-8")
    payloads.meta.write_text(
        json.dumps({"metadata": {"owner": "installed-test"}}),
        encoding="utf-8",
    )
    payloads.contract.write_text("Installed contract card\n", encoding="utf-8")
    return payloads


type InstalledMutation = tuple[list[str | Path], int, int | None]


def _generic_mutations() -> tuple[InstalledMutation, ...]:
    return (
        (
            [
                "state",
                "set",
                "--expected-revision",
                "0",
                'work.extensions["tests/installed"]',
                '{"items":[]}',
            ],
            1,
            None,
        ),
        (
            [
                "state",
                "append",
                "--expected-revision",
                "1",
                'work.extensions["tests/installed"].items',
                '"first"',
            ],
            2,
            None,
        ),
        (
            [
                "state",
                "delete",
                "--expected-revision",
                "2",
                'work.extensions["tests/installed"].items',
            ],
            3,
            None,
        ),
    )


def _task_start_mutations(payloads: InstalledPayloads) -> tuple[InstalledMutation, ...]:
    return (
        (
            ["state", "task", "add", "--expected-revision", "3", payloads.task],
            4,
            1,
        ),
        (
            ["state", "task", "start", "--expected-revision", "4", "1"],
            5,
            1,
        ),
        (
            [
                "state",
                "task",
                "attempt",
                "--expected-revision",
                "5",
                "1",
                payloads.attempt_one,
            ],
            6,
            1,
        ),
        (
            [
                "state",
                "task",
                "set-body",
                "--expected-revision",
                "6",
                "1",
                payloads.body,
            ],
            7,
            1,
        ),
    )


def _task_finish_mutations(
    payloads: InstalledPayloads,
) -> tuple[InstalledMutation, ...]:
    return (
        (
            [
                "state",
                "task",
                "set-meta",
                "--expected-revision",
                "7",
                "1",
                payloads.meta,
            ],
            8,
            1,
        ),
        (
            [
                "state",
                "task",
                "set-status",
                "--expected-revision",
                "8",
                "1",
                "in_progress",
            ],
            9,
            1,
        ),
        (
            [
                "state",
                "task",
                "complete",
                "--expected-revision",
                "9",
                "1",
                payloads.attempt_two,
            ],
            10,
            1,
        ),
    )


def _run_installed_mutations(
    console: list[Path],
    root: Path,
    cwd: Path,
    payloads: InstalledPayloads,
    installed_wheel: InstalledWheel,
) -> None:
    mutations = (
        *_generic_mutations(),
        *_task_start_mutations(payloads),
        *_task_finish_mutations(payloads),
    )
    for arguments, revision, result_value in mutations:
        _run_json_mutation(
            console,
            root,
            arguments,
            cwd=cwd,
            installed_wheel=installed_wheel,
            revision=revision,
            result_value=result_value,
        )


def _set_contract_and_capture_backup(
    console: list[Path],
    module: list[str | Path],
    root: Path,
    cwd: Path,
    contract: Path,
    installed_wheel: InstalledWheel,
) -> dict[str, object]:
    _run_json_mutation(
        console,
        root,
        [
            "state",
            "contract",
            "set",
            "--expected-revision",
            "10",
            contract,
        ],
        cwd=cwd,
        installed_wheel=installed_wheel,
        revision=11,
        result_value=None,
    )
    backup_state_result = _run(
        [*module, "--root", root, "state", "show"],
        cwd=cwd,
        installed_wheel=installed_wheel,
    )
    backup_state = json.loads(backup_state_result.stdout)
    assert backup_state["revision"] == 11
    assert backup_state["work"]["contract_card"] == "Installed contract card"
    assert len(backup_state["tasks"]) == 1
    return backup_state


def _assert_installed_restore(
    console: list[Path],
    module: list[str | Path],
    root: Path,
    cwd: Path,
    backup_state: dict[str, object],
    installed_wheel: InstalledWheel,
) -> None:
    _run_json_mutation(
        console,
        root,
        ["state", "task", "clear", "--expected-revision", "11"],
        cwd=cwd,
        installed_wheel=installed_wheel,
        revision=12,
        result_value=None,
    )
    _run_json_mutation(
        console,
        root,
        ["state", "restore", "--expected-revision", "12"],
        cwd=cwd,
        installed_wheel=installed_wheel,
        revision=13,
        result_value=None,
    )
    restored_result = _run(
        [*module, "--root", root, "state", "show"],
        cwd=cwd,
        installed_wheel=installed_wheel,
    )
    restored_state = json.loads(restored_result.stdout)
    expected_restored_state = {**backup_state, "revision": 13}
    assert restored_state == expected_restored_state


def _assert_default_human_output(
    console: list[Path],
    root: Path,
    cwd: Path,
    installed_wheel: InstalledWheel,
) -> None:
    progress = _run(
        [
            *console,
            "--root",
            root,
            "state",
            "set",
            "--expected-revision",
            "13",
            'work.extensions["tests/progress"]',
            "true",
        ],
        cwd=cwd,
        installed_wheel=installed_wheel,
    )
    assert progress.stdout == ""
    assert progress.stderr.strip()


def test_installed_entry_points_execute_every_state_command_from_hostile_cwd(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
) -> None:
    cwd = _hostile_cwd(tmp_path)
    root = (tmp_path / "project").resolve()
    root.mkdir()
    console = [installed_wheel.console_script]
    module = [installed_wheel.python, "-m", "ovcaq"]
    _assert_installed_reads(console, module, root, cwd, installed_wheel)
    payloads = _write_installed_payloads(tmp_path)
    _run_installed_mutations(console, root, cwd, payloads, installed_wheel)
    backup = _set_contract_and_capture_backup(
        console, module, root, cwd, payloads.contract, installed_wheel
    )
    _assert_installed_restore(console, module, root, cwd, backup, installed_wheel)
    _assert_default_human_output(console, root, cwd, installed_wheel)
