"""Read-only final integrity and evidence audit; prints the durable record."""

import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tomllib

ROOT = Path.cwd()
HEAD = "22d9193a0d00486b09ebea169e7a38a9f858799d"
BASE = "b43bf2c94d5eb0fddafca55542ef2570b45e8d52"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


assert git("rev-parse", "HEAD").strip() == HEAD
assert git("branch", "--show-current").strip() == "master"
assert git("status", "--porcelain=v1") == git("stash", "list") == ""
assert len(git("worktree", "list").splitlines()) == 1
assert len(git("for-each-ref", "--format=%(refname)", "refs/heads").splitlines()) == 1
assert git("diff", "HEAD", "--", "src", "tests", "docs", "AGENTS.md", "CHANGELOG.md") == ""
assert git("diff", "--check", f"{BASE}..{HEAD}") == ""

rev = ROOT / "dev/local/reviews"
tmp = ROOT / "dev/local/tmp"
prior = json.loads((rev / "00004-cycle-11-prior-artifact-hashes.json").read_text())
changed = [path for path, digest in prior.items() if not (ROOT / path).is_file() or sha(ROOT / path) != digest]
assert changed == [], changed
inventory = tomllib.loads((ROOT / "tests/characterization/current_system.toml").read_text())
migration = tomllib.loads((ROOT / "tests/characterization/migration.toml").read_text())
assert sha(ROOT / "dev/local/plans/implementation-plan.md") == migration["source_plan_sha256"]
assert sha(ROOT / "tests/characterization/current_system.toml") == migration["inventory_sha256"]
items = {row["id"]: row for row in inventory["items"]}
owned = [dict(items[ident], route=route) for route in migration["routes"] if route["owner_prd"] == "00004" for ident in route["ids"]]
join = json.loads((rev / "00004-cycle-11-owned-rows.json").read_text())
assert owned == join["owned"] and len(owned) == 55
assert len(join["source_tasks"]) == 10
review = (rev / "00004-workflow-core-v1-fast-review-11.md").read_text()
evidence = (rev / "00004-workflow-core-v1-fast-review-11-evidence.md").read_text()
verdicts = {}
for name, expected in {"alice": [f"R{i}" for i in (1,2,3,4,6,7,8,9,10,11,12,13)], "blake": [f"B{i}" for i in range(1,20)], "bob": [f"R{i}" for i in (1,2,3,4,6,7,8,9,10,11,12,13)] + [f"D{i}" for i in range(1,6)]}.items():
    output = (tmp / f"{name}-output-00004-cycle-11.txt").read_text()
    found = re.findall(r"^([RBD]\d+): (pass|fail)$", output, re.M)
    assert len(found) == len(expected) and {rule for rule, _ in found} == set(expected)
    assert output.strip() in review
    verdicts[name] = dict(found)
for row in owned:
    assert evidence.count(f"| {row['id']} |") == 1, row["id"]
assert "Verdict: 7 findings" in review
assert "Tests: 1339 passed, 0 failed, 0 skipped (suite run this cycle)" in review
probe = json.loads((rev / "00004-cycle-11-probes.json").read_text())
probe_root = Path(probe["argv"][0]).parents[2]
assert not probe_root.exists()
historical = ROOT / "dev/local/autopilot/state.json"
assert historical.stat().st_mtime == 1787864775.0302238
assert sha(historical) == "ed37670c08931fe703e21a7730f7d29bd1e242ae29d273cefd4abe506a23162f"
shape = subprocess.run(["python3", "/Users/bob/git/src/github.com/buvis/claude-autopilot/skills/review-work-completion/scripts/check_review_file.py", "--review-file", str(rev / "00004-workflow-core-v1-fast-review-11.md"), "--require-codex-guard"], capture_output=True, text=True, check=False)
assert shape.returncode == 0, shape.stderr
sizes = {}
for filename in ("workflow/_files.py", "workflow/records.py", "workflow/reports.py", "state/schema.py", "state/commands.py"):
    path = ROOT / "src/ovcaq" / filename
    sizes[str(path.relative_to(ROOT))] = {"lines": len(path.read_text().splitlines()), "max_function": max(n.end_lineno-n.lineno+1 for n in ast.walk(ast.parse(path.read_text())) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))}
print(json.dumps({"head": HEAD, "branch": "master", "status": "", "stashes": "", "worktrees": git("worktree", "list"), "tracked_tree_unchanged": True, "prior_files_checked": len(prior), "prior_changed": changed, "source_tasks": 10, "inventory_items": len(items), "owned_rows": 55, "plan_sha256": migration["source_plan_sha256"], "inventory_sha256": migration["inventory_sha256"], "review_sha256": sha(rev / "00004-workflow-core-v1-fast-review-11.md"), "raw_outputs_sha256": {name: sha(tmp / f"{name}-output-00004-cycle-11.txt") for name in verdicts}, "rubrics": verdicts, "sizes": sizes, "shape_gate": {"exit": shape.returncode, "stdout": shape.stdout, "stderr": shape.stderr}, "artifact_sha256": {str(path.relative_to(ROOT)): sha(path) for path in sorted((ROOT / "dist").glob("ovcaq-*"))}, "probe_root_removed": True, "preparation_bundle_removed": not Path("/tmp/ft04r11_inputs.json").exists(), "historical_state": {"prd": "00003-state-kernel-v1.md", "attached": False, "mtime_unchanged_from_initial_inspection": True, "sha256": sha(historical)}, "terminal_counts": {"FIX": 3, "VERIFY": 0, "KNOWN": 4, "total": 7}}, indent=2))
