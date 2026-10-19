from __future__ import annotations

import json
from pathlib import Path

from packaging_support import (
    InstalledWheel,
    _installed_workflow_root,
    _run,
    workflow_command,
)
from reports_scripts import UPDATE_REPORT_STATE


def _render_snapshot(
    installed: InstalledWheel, root: Path
) -> tuple[dict[str, str], str]:
    state_path = root / "docs/dev/project-management/ovcaq/state.json"
    before = state_path.read_bytes()
    result = _run(
        workflow_command(installed, root, "render", "report"),
        cwd=root,
        installed_wheel=installed,
    )
    value = json.loads(result.stdout)
    published = Path(value["path"]).read_bytes().decode("utf-8")
    assert state_path.read_bytes() == before
    return value, published


def _update_report_state(installed: InstalledWheel, root: Path, *values: str) -> None:
    _run(
        [installed.python, "-c", UPDATE_REPORT_STATE, root, *values],
        cwd=root,
        installed_wheel=installed,
    )


def test_installed_report_updates_return_complete_published_text(
    installed_wheel: InstalledWheel, tmp_path: Path
) -> None:
    root = _installed_workflow_root(installed_wheel, tmp_path)
    first = _render_snapshot(installed_wheel, root)
    first_replay = _render_snapshot(installed_wheel, root)
    path = Path(first[0]["path"])
    unrelated = "## Operator notes\n\nKeep café and žluťoučký.\n\n"
    stale = "## 00005-second.md\n\nStale B.\n\n## Batch Summary\n\nStale summary.\n\n"
    path.write_text(first[1] + "\n" + unrelated + stale * 2, encoding="utf-8")
    _update_report_state(
        installed_wheel, root, "00005-second.md", "review", "review", "2"
    )
    second = _render_snapshot(installed_wheel, root)
    second_replay = _render_snapshot(installed_wheel, root)
    old_a = first[1].split("## Batch Summary")[0].split("\n\n", 1)[1]
    path.write_text(second[1] + "\n" + old_a * 2, encoding="utf-8")
    _update_report_state(
        installed_wheel, root, "00004-workflow-core-v1.md", "done", "", "5"
    )
    third = _render_snapshot(installed_wheel, root)
    third_replay = _render_snapshot(installed_wheel, root)
    snapshots = [first, first_replay, second, second_replay, third, third_replay]

    assert [value["text"] for value, _ in snapshots] == [text for _, text in snapshots]
    assert [value["path"] for value, _ in snapshots] == [str(path)] * 6
    assert [first, second, third] == [first_replay, second_replay, third_replay]
    assert old_a in second[1]
    assert unrelated in second[1]
    assert unrelated in third[1]
    assert "Stale" not in second[1]
    assert "- Total cycles: 2\n" in second[1]
    assert "- Total cycles: 5\n" in third[1]
    assert "- Total cycles: 2\n" not in third[1]
    assert old_a not in third[1]
    assert "- Phase: done\n- Next phase: drained\n- Tasks: 1/1\n" in third[1]
    b_section = (
        "## 00005-second.md\n\n- Phase: review\n- Next phase: review\n- Tasks: 1/1\n"
    )
    assert b_section in second[1]
    assert b_section in third[1]
    assert third[1].count("## 00004-workflow-core-v1.md\n") == 1
    assert second[1].count("## 00005-second.md\n") == 1
    assert third[1].count("## 00005-second.md\n") == 1
    assert second[1].count("## Batch Summary\n") == 1
    assert third[1].count("## Batch Summary\n") == 1
