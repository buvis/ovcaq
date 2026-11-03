"""Prepare isolated review inputs without touching product or prior evidence."""

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib
import tempfile

OUTPUTS = {}

ROOT = Path.cwd()
BASE = "b43bf2c94d5eb0fddafca55542ef2570b45e8d52"
HEAD = "22d9193a0d00486b09ebea169e7a38a9f858799d"
PACK = Path("/Users/bob/git/src/github.com/buvis/claude-autopilot")
SKILL = PACK / "skills/review-work-completion"
TMP = ROOT / "dev/local/tmp"
REV = ROOT / "dev/local/reviews"
TAG = "00004-cycle-11"
PRD = ROOT / "dev/local/prds/wip/00004-workflow-core-v1.md"


def run(argv):
    return subprocess.run(argv, text=True, capture_output=True, check=True).stdout


def write(path, text):
    OUTPUTS[str(path)] = text


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert run(["git", "rev-parse", "HEAD"]).strip() == HEAD
assert run(["git", "status", "--porcelain=v1"]) == ""
assert os.access(PACK / "skills/use-codex/scripts/codex-run.sh", os.X_OK)
plan_path = ROOT / "dev/local/plans/implementation-plan.md"
inventory_path = ROOT / "tests/characterization/current_system.toml"
migration = tomllib.loads((ROOT / "tests/characterization/migration.toml").read_text())
inventory = tomllib.loads(inventory_path.read_text())
assert sha(plan_path) == migration["source_plan_sha256"]
assert sha(inventory_path) == migration["inventory_sha256"]
items = {row["id"]: row for row in inventory["items"]}
owned = [dict(items[ident], route=route) for route in migration["routes"]
         if route["owner_prd"] == "00004" for ident in route["ids"]]
assert len(owned) == len({row["id"] for row in owned}) == 55
plan = plan_path.read_text()
phase = plan.split("### Phase 2 — deterministic workflow core\n", 1)[1].split("### Phase 3", 1)[0]
tasks = re.findall(r"- \[ \] \[(P02-T\d+)\] (.*?)(?=\n- \[ \]|\n\nExit criteria:)", phase, re.S)
assert [ident for ident, _ in tasks] == [f"P02-T{n:02d}" for n in range(1, 11)]
exits = phase.split("Exit criteria:\n", 1)[1].strip()
source = {
    "head": HEAD, "base": BASE, "plan_sha256": sha(plan_path),
    "inventory_sha256": sha(inventory_path), "source_tasks": tasks,
    "phase_exits_verbatim": exits, "owned": owned,
}
write(REV / f"{TAG}-owned-rows.json", json.dumps(source, indent=2) + "\n")
TMP.mkdir(exist_ok=True)
task_text = "# Source tasks — standalone FT-04R11\n\nNo autopilot task store is attached. All ten source obligations remain.\n\n| Task | Verbatim source task | Initial shared commit |\n|---|---|---|\n"
for i, (ident, description) in enumerate(tasks):
    commit = "06fdf88149a7cafd6d3f4ec9aedf1510a59a652a" if i < 5 else "5a7ff023059bd396a177da7946a25ffe8d6d176d"
    task_text += f"| {ident} | {description.replace(chr(10), ' ')} | {commit}; shared with {'P02-T01–T05' if i < 5 else 'P02-T06–T10'} |\n"
task_text += f"\n## Source phase exit criteria (verbatim)\n\n{exits}\n\n## Full implementation commits\n\n" + run(["git", "log", "--reverse", "--format=%H %s", f"{BASE}..{HEAD}"])
write(TMP / f"review-tasks-{TAG}.md", task_text)
write(TMP / f"review-prd-{TAG}.md", PRD.read_text())
with tempfile.TemporaryDirectory(prefix="ft04r11-context-") as temporary:
    staging = Path(temporary)
    helper = (SKILL / "scripts/gather-context.sh").read_text().replace('TMP_DIR="$PROJECT_ROOT/dev/local/tmp"', 'TMP_DIR="' + temporary + '"')
    helper_path = staging / "gather-context.sh"
    helper_path.write_text(helper)
    for filename in (f"review-tasks-{TAG}.md", f"review-prd-{TAG}.md"):
        (staging / filename).write_text(OUTPUTS[str(TMP / filename)])
    run(["bash", str(helper_path), "--since", BASE, str(staging / f"review-tasks-{TAG}.md"), str(staging / f"review-prd-{TAG}.md")])
    context_path = TMP / f"review-context-{TAG}.md"
    context = (staging / context_path.name).read_text().replace(temporary, str(TMP)).replace(f"incremental review (changes since {BASE})", f"full implementation review ({BASE}..{HEAD}); explicit base supplied with --since")
    write(TMP / f"review-diff-{TAG}.diff", (staging / f"review-diff-{TAG}.diff").read_text())
changed = run(["git", "diff", "--name-only", BASE, HEAD]).splitlines()
blocks = []
for helper in ("compute_mech_facts.py", "detect_tautological_tests.py"):
    blocks.append(run([sys.executable, str(SKILL / "scripts" / helper), *changed]))
blocks.append("## Implementation-base replay\n\nreplay: skipped (retained missing packaging_support collection failure). User explicitly forbids retry of that dead end. Prior bounded repair-base replay: 56 collected, 46 failed, 10 valid preservation cases passed. R9 repair supplies 23 chronological fail-first cases; no universal full-range binding follows. See R9 evidence companion for exact limitations.\n")
source_inputs = "\n".join(str(ROOT / p) for p in [
    "AGENTS.md", "dev/local/plans/implementation-plan.md",
    "dev/local/prds/implementation-plan-coverage.md", "dev/local/discovery/00001-ovcaq-v1.md",
    "tests/characterization/current_system.toml", "tests/characterization/migration.toml"])
context += "\n## Mandatory source contract\n\n" + source_inputs + f"\n\nFresh full 55-row join: {REV / (TAG + '-owned-rows.json')}\n"
context += "\n".join(blocks)
context += "\n## Execution scope\n\nStandalone fresh FT-04R11. No attached task/attempt ledger, no unrelated autopilot state. All source tasks, owned rows, and phase exits remain required. No design doc. Retrieval pack availability is recorded separately; no capsule refresh authorized. No external Bob/Carl wrapper retry or guard bypass. Native prompt isolation does not establish model diversity. Coordinator runs full verification this cycle.\n"
write(context_path, context)
dimensions = (SKILL / "references/review-dimensions.md").read_text()
rubric = (SKILL / "references/rubric.md").read_text()
formats = (SKILL / "references/output-formats.md").read_text().split("## Agent Output Format (Single Source of Truth)\n", 1)[1].split("## Per-Rule Verdict Format", 1)[0]
settled = """
## Settled scope decisions
Preserve R8-K1 (inherited collision OR assertion), R8-K2 (53-line add_task), R9-K3 (inherited schema size) and R9-K4 (full-base replay limitation) as KNOWN. No broad state/replay-tool restructuring. Three inherited packaging overlength functions remain unchanged from base.
Initially absent source intentionally keeps null artifact and failure evidence; later unidentified replacement remains refused. No abort/rollback API.
Frontmatter returns policy controls to its downstream runtime owner; no fabricated catchup/design completion or duplicate durable policy.
No importer, aliases, launcher markers, provider/model policy, Linux qualification, PRD closeout, next PRD, capsule refresh or implementation-plan edit. Keep terminal drain and all preservation invariants.
These decisions are user constraints; raise a NEW finding only if its settled reason no longer holds.
"""
host = """
## Host execution contract
This is a native isolated host context with the installed persona body. No model diversity is claimed. Do not spawn reviewers or invoke external CLIs. Review only: no source/test/document edits, Git mutations or state mutations. Read-only shell search/read is the available file-inspection adapter; Bob remains static-only and must not execute product code or verification. Alice/Blake may use disposable probes with context-managed roots and reaped children; coordinator owns full gates. Return your complete review in your final response; never write a reviewer output file. Do not inspect other reviewers' prompts/results or earlier review history except the explicitly supplied Alice repair evidence. Work only in the specified repository. Tools may require a one-sentence fact-forcing preamble before your first read command.
"""
for name in ("alice", "blake", "bob"):
    persona = (PACK / f"agents/{name}.md").read_text()
    header, body = persona.split("---", 2)[1:]
    assert f"name: {name}" in header and "description:" in header
    substitutions = {
        "{CONTEXT_FILE}": str(context_path), "{DIFF_FILE}": str(TMP / f"review-diff-{TAG}.diff"),
        "{PACK_FILE}": "(no pack available this cycle)", "{PACK_FINDINGS}": "(no pack available this cycle)",
        "{REVIEW_CHECKLIST}": dimensions, "{RUBRIC}": rubric,
        "{OUTPUT_FORMAT}": formats.replace("{AGENT_NAME}", name.upper()), "{PRD}": PRD.read_text(),
    }
    if name == "blake":
        substitutions["{RUBRIC}"] = (PACK / "skills/review-blindly/references/rubric.md").read_text()
    for key, value in substitutions.items():
        body = body.replace(key, value)
    if name == "bob":
        eve = (PACK / "agents/eve.md").read_text()
        body += "\n## Two lenses, applied to every changed file\n" + eve.split("## Two lenses, applied to every changed file\n", 1)[1].replace("{PACK_FINDINGS}", "(no pack available this cycle)")
        body += "\n" + (PACK / "skills/run-autopilot/references/doubt-review-rubric.md").read_text()
    if name != "blake":
        body += settled
    if name == "alice":
        body += "\n## Authorized repair evidence\nVerify R10-01 complete report result equality including installed A→B→A/replays. Verify all R9-01–R9-05 repairs, including coordinator-only lock root regardless of prior votes, and preserve R8 guarantees. Read these files:\n" + "\n".join(str(ROOT / p) for p in [
            "dev/local/reviews/00004-workflow-core-v1-fast-review-10.md",
            "dev/local/reviews/00004-workflow-core-v1-fast-review-10-evidence.md",
            "dev/local/plans/fast-track-handoffs/00004-workflow-core-v1/rework-10.md",
            "dev/local/plans/fast-track-handoffs/00004-workflow-core-v1/review-10.md",
            "dev/local/reviews/00004-workflow-core-v1-fast-review-09.md",
            "dev/local/reviews/00004-workflow-core-v1-fast-review-09-evidence.md",
            "dev/local/plans/fast-track-handoffs/00004-workflow-core-v1/rework-09.md",
            "dev/local/plans/fast-track-handoffs/00004-workflow-core-v1/review-09.md"])
    if name == "blake":
        body += f"\n## Source specification paths\nRepository: {ROOT}\nCanonical PRD: {PRD}\nRead its accepted plan, coverage, discovery and both characterization TOMLs. These are specification sources, not implementation history. Phase B15/B16/B17 map to PRD A/B/C.\n"
    body += host
    write(TMP / f"{name}-prompt-{TAG}.md", body)
prior = [p for parent in (ROOT / "dev/local/reviews", ROOT / "dev/local/plans", ROOT / "dev/local/tmp") for p in parent.rglob("*") if p.is_file() and "cycle-11" not in p.name and "review-11" not in p.name]
snapshot = {str(p.relative_to(ROOT)): sha(p) for p in prior}
snapshot[str(PRD.relative_to(ROOT))] = sha(PRD)
write(REV / f"{TAG}-prior-artifact-hashes.json", json.dumps(snapshot, indent=2) + "\n")
for destination, content in OUTPUTS.items():
    assert not Path(destination).exists(), destination
bundle = Path("/tmp/ft04r11_inputs.json")
bundle.write_text(json.dumps(OUTPUTS))
print(json.dumps({"bundle": str(bundle), "files": list(OUTPUTS), "inventory_items": len(items), "autopilot_state_exists": (ROOT / "dev/local/autopilot/state.json").exists(), "settled_ledger_exists": (REV / "00004-workflow-core-v1-ledger.json").exists(), "design_exists": (ROOT / "dev/local/designs/00004-workflow-core-v1-design.md").exists(), "capsule_exists": (ROOT / "dev/local/meta/project-capsule.md").exists(), "head": HEAD, "changed_files": len(changed), "source_tasks": len(tasks), "owned_rows": len(owned), "source_hashes_verified": True, "prompts": [str(TMP / f"{name}-prompt-{TAG}.md") for name in ("alice", "blake", "bob")], "filesystem_notes_trigger": (ROOT / "dev/local").is_symlink() or ROOT.name.startswith(".")}, indent=2))
