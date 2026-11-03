"""Prime the authorized recovery; canonical phase-done commits the handoff."""

import ast
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLUGIN = Path("/Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.5.1/skills/run-autopilot")
sys.path.insert(0, str(PLUGIN))
from cli import schema, statectl


def prepare(state):
    assert state["phase"] == state["next_phase"] == "paused"
    assert state["pause_reason"]["site"] == "data_loss_risk"
    assert state["cycle"] == 13 and state["rework_cap"] == 2
    assert state["tasks_completed"] == state["tasks_total"] == 16
    assert state["rework_task_ids"] == ["4", "5", "6"]
    assert "review" not in state["phases_completed"]
    assert all(task["status"] == "completed" for task in state["tasks"])
    original = json.loads((ROOT / "dev/local/reviews/00004-cycle-13-pre-repair-state.json").read_text())
    assert state["batch"] == original["batch"]
    assert state["prd"] == original["prd"]
    original_tasks = {task["id"]: task for task in original["tasks"]}
    for task in state["tasks"]:
        if task["id"] not in {"4", "5", "6"}:
            assert task == original_tasks[task["id"]]
        else:
            assert task["attempts"][-1]["outcome"] == "completed"
            assert task["attempts"][-1]["review_cycle"] == 13
    verification = json.loads((ROOT / "dev/local/autopilot/last-verification.json").read_text())
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert verification["sha"] == head and verification["cycle"] == 13
    assert len(verification["commands"]) >= 6
    assert all(command["exit"] == 0 for command in verification["commands"])
    assert verification["failed"] in (0, None)
    if verification["passed"] is None:
        prior = json.loads((ROOT / "dev/local/reviews/00004-cycle-13-verification-before-format.json").read_text())
        assert prior["passed"] == 1359 and prior["failed"] == 0
        path = "src/ovcaq/workflow/_files.py"
        changed = subprocess.check_output(["git", "diff", "--name-only", prior["sha"], head], cwd=ROOT, text=True).splitlines()
        assert changed == [path]
        before = subprocess.check_output(["git", "show", prior["sha"] + ":" + path], cwd=ROOT, text=True)
        assert ast.dump(ast.parse(before)) == ast.dump(ast.parse((ROOT / path).read_text()))
    else:
        assert verification["passed"] > 1352
    assert subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT) == b""
    assert (ROOT / "dev/local/reviews/00004-cycle-13-repair-report.md").is_file()
    state["autonomous_decisions"].append({
        "cycle": 13,
        "attempt": "20260913-interactive-repair-complete",
        "issue": "Operator-authorized tasks 4–6 completed and verified",
        "severity": "high", "consensus": "operator", "action": "resume_review",
        "reason": "Original replacement probe now refuses with retryable identity error; task tests, deeper installed probes, real launcher sandbox checks and full suite passed. Restore review origin for canonical phase-done rework. Cap stays 2; all prior evidence remains. Next review must be fresh.",
        "evidence": "dev/local/reviews/00004-cycle-13-repair-report.md",
    })
    # A crash before phase-done leaves the wrapper paused, with rework IDs intact.
    state["phase"] = "review"
    del state["pause_reason"]
    schema.validate(state)


if __name__ == "__main__":
    statectl.mutate(ROOT / "dev/local/autopilot/state.json", prepare)
    print(json.dumps({"phase": "review", "next_phase": "paused", "next_command": "phase-done --outcome rework"}))
