"""Audit the review record and prove prior evidence/source preservation."""

import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path.cwd()
REV = ROOT / "dev/local/reviews"
TMP = ROOT / "dev/local/tmp"
TAG = "00004-cycle-10"
HEAD = "72562f6fd12fb039e91e4c7b1be29758d1901ec8"
review = REV / "00004-workflow-core-v1-fast-review-10.md"
evidence = REV / "00004-workflow-core-v1-fast-review-10-evidence.md"
handoff = ROOT / "dev/local/plans/fast-track-handoffs/00004-workflow-core-v1/review-10.md"
target = REV / f"{TAG}-final-audit.json"


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert git("rev-parse", "HEAD").strip() == HEAD
assert git("branch", "--show-current").strip() == "master"
assert git("status", "--porcelain=v1") == ""
assert git("stash", "list") == ""
worktrees = git("worktree", "list", "--porcelain")
assert worktrees.count("worktree ") == 1 and str(ROOT) in worktrees
prior = json.loads((REV / f"{TAG}-prior-artifact-hashes.json").read_text())
changed_prior = [name for name, digest in prior.items() if not (ROOT / name).is_file() or sha(ROOT / name) != digest]
assert not changed_prior, changed_prior
source = json.loads((REV / f"{TAG}-owned-rows.json").read_text())
assert sha(ROOT / "dev/local/plans/implementation-plan.md") == source["plan_sha256"]
assert sha(ROOT / "tests/characterization/current_system.toml") == source["inventory_sha256"]
body = review.read_text()
ev = evidence.read_text()
owned_ids = re.findall(r"^\| ((?:ART|CMD|DEC|ENV|STATE|TEST)-\d+) \|", ev, re.M)
tasks = re.findall(r"^\| (P02-T\d+) \|", ev, re.M)
assert len(owned_ids) == len(set(owned_ids)) == 55
assert set(owned_ids) == {row["id"] for row in source["owned"]}
assert tasks == [f"P02-T{n:02d}" for n in range(1, 11)]
assert "Verdict: 5 findings" in body
assert body.rstrip().endswith("Tests: 1338 passed, 0 failed, 0 skipped (suite run this cycle)")
verdicts = {}
for name, next_name, prefixes in [
    ("alice", "Blake", {"R": {1,2,3,4,6,7,8,9,10,11,12,13}}),
    ("blake", "Bob", {"B": set(range(1,20))}),
    ("bob", "Handoff", {"R": {1,2,3,4,6,7,8,9,10,11,12,13}, "D": set(range(1,6))}),
]:
    raw = (TMP / f"{name}-output-{TAG}.txt").read_text().strip()
    section = body.split(f"## {name.title()}\n", 1)[1].split(f"\n## {next_name}\n", 1)[0]
    assert raw in section, name
    found = re.findall(r"^([RBD])(\d+): (pass|fail)$", raw, re.M)
    assert len(found) == sum(map(len, prefixes.values()))
    for prefix, numbers in prefixes.items():
        assert {int(number) for kind, number, _ in found if kind == prefix} == numbers
    verdicts[name] = {kind+number: value for kind, number, value in found}
gate_argv = [sys.executable, "/Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.5.0/skills/review-work-completion/scripts/check_review_file.py", "--review-file", str(review), "--require-codex-guard"]
gate = subprocess.run(gate_argv, capture_output=True, text=True, check=False)
assert gate.returncode == 0, gate.stderr + gate.stdout
missing = []
for path in (review, evidence, handoff, REV / f"{TAG}-contract-card.md"):
    for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
        link = link.split("#", 1)[0]
        if not link or "://" in link:
            continue
        resolved = (path.parent / link).resolve()
        if resolved != target and not resolved.exists():
            missing.append({"file": str(path.relative_to(ROOT)), "target": link})
assert not missing, missing
artifacts = sorted({*REV.glob("*cycle-10*"), *REV.glob("00004-workflow-core-v1-fast-review-10*"), *TMP.glob("*00004-cycle-10*"), handoff})
hashes = {str(path.relative_to(ROOT)): sha(path) for path in artifacts if path.is_file() and path != target}
result = {
    "at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "head": HEAD,
    "branch": "master", "git_status": "", "stashes": "", "worktrees": worktrees,
    "source_tasks": tasks, "owned_rows": owned_ids, "owned_row_count": 55,
    "source_hashes": {"plan": source["plan_sha256"], "inventory": source["inventory_sha256"]},
    "prior_artifacts_checked": len(prior), "changed_prior_artifacts": changed_prior,
    "rubric_verdicts": verdicts, "raw_outputs_retained_verbatim": True,
    "review_shape_gate": {"argv": gate_argv, "exit": gate.returncode, "stdout": gate.stdout, "stderr": gate.stderr},
    "missing_artifact_links": missing, "terminal": {"fix": 1, "verify": 0, "known": 4, "total": 5},
    "review_only": True, "tracked_changes": git("diff", "--name-only", "HEAD"),
    "cleanup": "No worktree, branch or executed plan created; disposable roots and subprocesses context-managed/reaped. Review evidence and builds intentionally retained; other sessions' files untouched.",
    "artifact_sha256": hashes,
}
target.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"head": HEAD, "shape_gate": gate.returncode, "source_tasks": len(tasks), "owned_rows": len(owned_ids), "prior_artifacts_unchanged": len(prior), "tracked_changes": result["tracked_changes"], "missing_links": missing, "terminal": result["terminal"]}, indent=2))
