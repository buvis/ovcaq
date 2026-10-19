from __future__ import annotations

import json
import os
import socket
import subprocess
from pathlib import Path

import pytest
from packaging_support import (
    InstalledWheel,
    _installed_workflow_root,
    _run,
    _run_unchecked,
)
from reports_scripts import (
    COMPLETED_SUMMARY,
    POISON_PRD,
    SET_BATCH,
)


@pytest.mark.parametrize("kind", ("fifo", "directory", "socket"))
def test_installed_report_nonregular_target_fails_promptly(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
    kind: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    target = (
        root / "docs/dev/project-management/ovcaq/reports/installed-batch-report.md"
    )
    target.parent.mkdir()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        if kind == "fifo":
            os.mkfifo(target)
        elif kind == "directory":
            target.mkdir()
        else:
            monkeypatch.chdir(target.parent)
            listener.bind(target.name)
        before = target.lstat()
        result = subprocess.run(
            [
                str(installed_wheel.console_script),
                "--root",
                str(root),
                "--json",
                "workflow",
                "render",
                "report",
            ],
            cwd=root,
            env=installed_wheel.environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=3,
        )

    assert result.returncode == 2
    assert json.loads(result.stderr)["error"]["code"] == "state_io"
    assert target.lstat().st_ino == before.st_ino
    assert target.lstat().st_mode == before.st_mode
    assert list(target.parent.iterdir()) == [target]


def _equal_key_rows(event: str) -> list[dict[str, object]]:
    common = {"batch": "installed-batch", "prd": "00004-workflow-core-v1.md"}
    rows = (
        [
            {
                **common,
                "phase_launched": "build",
                "ts_start": 1,
                "signal": "continue",
                "wall_secs": 2,
            },
            {
                **common,
                "phase_launched": "build",
                "ts_start": 1,
                "signal": "done",
                "tokens_out": 5,
            },
        ]
        if event == "session"
        else [
            {
                **common,
                "event": "review_converged",
                "ts": 2,
                "cycles_to_converge": 1,
                "outcome": "converged",
            },
            {
                **common,
                "event": "review_converged",
                "ts": 2,
                "cycles_to_converge": 3,
                "outcome": "other",
            },
        ]
    )
    return rows


@pytest.mark.parametrize("event", ("session", "convergence"))
def test_installed_metrics_order_is_stable_when_primary_keys_collide(
    installed_wheel: InstalledWheel, tmp_path: Path, event: str
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    rows = _equal_key_rows(event)
    ledger = root / "docs/dev/project-management/ovcaq/metrics.jsonl"
    command = [
        installed_wheel.console_script,
        "--root",
        root,
        "--json",
        "workflow",
        "render",
        "metrics",
    ]
    ledger.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    first = _run(command, cwd=root, installed_wheel=installed_wheel)
    ledger.write_text(
        "".join(json.dumps(row) + "\n" for row in reversed(rows)), encoding="utf-8"
    )
    second = _run(command, cwd=root, installed_wheel=installed_wheel)
    assert first.stdout == second.stdout


@pytest.mark.parametrize(
    ("shape", "count", "cycles", "applied", "escalated"),
    (
        ("empty", 0, "0", "0", "0"),
        ("rich", 1, "2", "4", "1"),
        ("legacy", 1, "unknown", "unknown", "unknown"),
        ("mixed", 2, "unknown", "unknown", "unknown"),
        ("legacy-name", 1, "unknown", "unknown", "unknown"),
        ("mixed-name", 2, "unknown", "unknown", "unknown"),
    ),
)
def test_installed_report_completed_summary_contract(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
    shape: str,
    count: int,
    cycles: str,
    applied: str,
    escalated: str,
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    script = COMPLETED_SUMMARY
    result = _run(
        [installed_wheel.python, "-c", script, root, shape],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    text = json.loads(result.stdout)["text"]
    assert f"- PRDs completed: {count}" in text
    assert f"- Total cycles: {cycles}" in text
    assert f"- Applied decisions: {applied}" in text
    assert f"- Escalated decisions: {escalated}" in text
    assert Path(json.loads(result.stdout)["path"]).read_text(encoding="utf-8") == text


def test_installed_report_rejects_traversal_and_symlinked_output_parent(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
) -> None:
    root = tmp_path / "installed-report-confinement"
    root.mkdir()
    _run(
        [installed_wheel.console_script, "--root", root, "--json", "init"],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    set_batch = SET_BATCH
    _run(
        [installed_wheel.python, "-c", set_batch, root, "../escaped"],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    command = [
        installed_wheel.console_script,
        "--root",
        root,
        "--json",
        "workflow",
        "render",
        "report",
    ]
    traversal = _run_unchecked(command, cwd=root, installed_wheel=installed_wheel)
    assert traversal.returncode == 1
    assert "batch" in traversal.stderr
    runtime = root / "docs/dev/project-management/ovcaq"
    assert not (runtime / "escaped-report.md").exists()

    _run(
        [installed_wheel.python, "-c", set_batch, root, "safe"],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    external = tmp_path / "installed-external-reports"
    external.mkdir()
    sentinel = external / "safe-report.md"
    sentinel.write_text("sentinel\n", encoding="utf-8")
    (runtime / "reports").symlink_to(external, target_is_directory=True)
    symlinked = _run_unchecked(command, cwd=root, installed_wheel=installed_wheel)

    assert symlinked.returncode == 2
    assert json.loads(symlinked.stderr)["error"]["code"] == "state_io"
    assert sentinel.read_text(encoding="utf-8") == "sentinel\n"


def _write_metrics(runtime: Path) -> None:
    rows = (
        {
            "ts_start": 1,
            "ts_end": 13,
            "wall_secs": 12,
            "prd": "00004-workflow-core-v1.md",
            "batch": "installed-batch",
            "phase_launched": "build",
            "phase_end": "build",
            "signal": "continue",
            "model": "build-tier",
            "cost_usd": 0.12,
            "tokens_out": 10,
        },
        {
            "event": "review_converged",
            "prd": "00004-workflow-core-v1.md",
            "batch": "installed-batch",
            "cycles_to_converge": 2,
            "outcome": "converged",
            "ts": 14,
        },
    )
    runtime.joinpath("metrics.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_installed_render_consumes_metrics_and_rejects_control_headings(
    installed_wheel: InstalledWheel,
    tmp_path: Path,
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    runtime = root / "docs/dev/project-management/ovcaq"
    _write_metrics(runtime)
    prefix = [installed_wheel.console_script, "--root", root, "--json", "workflow"]

    metrics = _run(
        [*prefix, "render", "metrics"],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    assert "- Wall seconds: 12" in json.loads(metrics.stdout)["text"]
    report = _run(
        [*prefix, "render", "report"],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    report_path = Path(json.loads(report.stdout)["path"])
    assert "- Cycles to converge: 2" in report_path.read_text(encoding="utf-8")
    report_before = report_path.read_bytes()

    poison_script = POISON_PRD
    _run(
        [installed_wheel.python, "-c", poison_script, root],
        cwd=root,
        installed_wheel=installed_wheel,
    )
    rejected = _run_unchecked(
        [*prefix, "render", "report"],
        cwd=root,
        installed_wheel=installed_wheel,
    )

    assert rejected.returncode == 1
    error = json.loads(rejected.stderr)["error"]
    assert error["code"] == "usage"
    assert "work.prd" in error["message"]
    assert "StopIteration" not in rejected.stderr
    assert report_path.read_bytes() == report_before
