import datetime, hashlib, json, re, subprocess, tomllib
from pathlib import Path

root=Path.cwd()
def git(*args):
    r=subprocess.run(["git",*args],capture_output=True,text=True,check=True)
    return r.stdout
head=git("rev-parse","HEAD").strip()
status=git("status","--porcelain=v1")
branch=git("branch","--show-current").strip()
stashes=git("stash","list")
worktrees=git("worktree","list","--porcelain")
assert head=="78f916c366f74105b76e6f07d80a7a1aeb251e9f"
assert status=="" and stashes=="" and branch=="master"
assert worktrees.count("worktree ")==1 and str(root) in worktrees
reviews=root/"dev/local/reviews"
main=reviews/"00004-workflow-core-v1-fast-review-09.md"
evidence=reviews/"00004-workflow-core-v1-fast-review-09-evidence.md"
body=main.read_text(); ev=evidence.read_text()
owned=json.loads((reviews/"00004-cycle-09-owned-rows.json").read_text())
if isinstance(owned,dict):
    owned=owned["owned"]
owned_ids={r["id"] for r in owned}
row_ids=re.findall(r"^\| ((?:ART|CMD|DEC|ENV|STATE|TEST)-\d+) \|",ev,re.M)
assert len(owned_ids)==len(row_ids)==55 and set(row_ids)==owned_ids
task_ids=re.findall(r"^\| (P02-T\d+) \|",ev,re.M)
assert task_ids==[f"P02-T{n:02d}" for n in range(1,11)]
rubrics={}
for name,next_name,prefixes in [
    ("alice","Blake",{"R":{1,2,3,4,6,7,8,9,10,11,12,13}}),
    ("blake","Bob",{"B":set(range(1,20))}),
    ("bob","Handoff",{"R":{1,2,3,4,6,7,8,9,10,11,12,13},"D":set(range(1,6))}),
]:
    raw=(root/f"dev/local/tmp/{name}-output-00004-cycle-09.txt").read_text().strip()
    section=body.split(f"## {name.title()}\n",1)[1].split(f"\n## {next_name}\n",1)[0]
    assert raw in section, name
    verdicts=re.findall(r"^([RBD])(\d+): (pass|fail)$",raw,re.M)
    assert len(verdicts)==sum(map(len,prefixes.values()))
    for prefix,numbers in prefixes.items():
        assert {int(n) for p,n,v in verdicts if p==prefix}==numbers
    rubrics[name]={p+n:v for p,n,v in verdicts}
assert "Verdict: 9 findings" in body
assert "Tests: 1315 passed, 0 failed, 0 skipped (suite run this cycle)" in body
plan=root/"dev/local/plans/implementation-plan.md"
inventory=root/"tests/characterization/current_system.toml"
digests={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (plan,inventory)}
assert digests[str(plan.relative_to(root))]=="43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5"
assert digests[str(inventory.relative_to(root))]=="d2a839b6c3b43c00c66114e0f20fe0d85b6169449562a72cf41ae30768eefdb9"
files=sorted(set(
    list(reviews.glob("*cycle-09*"))
    +list(reviews.glob("00004-workflow-core-v1-fast-review-09*"))
    +list((root/"dev/local/tmp").glob("*00004-cycle-09*"))
    +[root/"dev/local/plans/fast-track-handoffs/00004-workflow-core-v1/review-09.md"]
))
pending=reviews/"00004-cycle-09-final-audit.json"
missing_links=[]
copied_source_links=[]
for path in files:
    if path.suffix!=".md":continue
    for target in re.findall(r"\]\(([^)]+)\)",path.read_text()):
        target=target.split("#",1)[0]
        if not target or "://" in target:continue
        if not (path.parent/target).exists() and (path.parent/target).resolve()!=pending:
            original_prd=root/"dev/local/prds/wip/00004-workflow-core-v1.md"
            copied_targets={"../../plans/implementation-plan.md","../implementation-plan-coverage.md","../../discovery/00001-ovcaq-v1.md"}
            if path.parent==root/"dev/local/tmp" and target in copied_targets:
                resolved=(original_prd.parent/target).resolve()
                assert resolved.exists()
                copied_source_links.append({"file":str(path.relative_to(root)),"target":target,"original_prd_resolution":str(resolved.relative_to(root))})
            else:
                missing_links.append({"file":str(path.relative_to(root)),"target":target})
assert not missing_links, missing_links
artifact_hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file() and p!=pending}
print(json.dumps({
    "at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "head":head,"branch":branch,"status":status,"stashes":stashes,"worktrees":worktrees,
    "ten_tasks":task_ids,"owned_row_count":len(row_ids),"rubric_verdicts":rubrics,
    "raw_outputs_retained":True,"source_hashes":digests,"missing_artifact_links":missing_links,"copied_source_links":copied_source_links,
    "review_only":True,"terminal":{"fix":5,"verify":0,"known":4,"total":9},
    "tracked_changes":git("diff","--name-only","HEAD"),
    "artifact_sha256":artifact_hashes,
    "audit_scope_adjustment":"Copied PRD links resolve against the canonical WIP PRD, preserving dispatched prompts. New review/handoff links resolve against each artifact.",
},indent=2))
