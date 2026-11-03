"""Preserve observed native worker metadata for the next isolated review."""

import hashlib
import json
import re
from pathlib import Path

repo = Path.cwd()
parent = "01a1110c-ab32-7331-ba24-97568ff1aaf9"
out = repo / "docs/dev/project-management/autopilot/worker-sessions"
out.mkdir(exist_ok=True)
rows = []
noncontributors = {"tess19", "tess25", "ivan21", "deslop24", "deslop26", "ivan28_hygiene"}
for path in Path("/Users/bob/.codex/sessions/2026/10/06").glob("*.jsonl"):
    lines = path.read_bytes().splitlines()
    if not lines:
        continue
    meta = json.loads(lines[0]).get("payload", {})
    source = meta.get("source", {})
    if not isinstance(source, dict):
        continue
    spawn = source.get("subagent", {}).get("thread_spawn", {})
    if spawn.get("parent_thread_id") != parent:
        continue
    agent = spawn["agent_path"].rsplit("/", 1)[-1]
    match = re.search(r"\d+", agent)
    if not match:
        raise ValueError(f"Unknown worker role: {agent}")
    target = out / path.name
    target.write_bytes(path.read_bytes())
    target.chmod(0o600)
    observations = []
    for number, line in enumerate(lines, 1):
        record = json.loads(line)
        if record.get("type") != "turn_context":
            continue
        payload = record["payload"]
        observations.append({
            "model": payload.get("model"),
            "effort": payload.get("effort"),
            "line": number,
            "sha256": hashlib.sha256(line).hexdigest(),
        })
    rows.append({
        "task": match[0],
        "agent": spawn["agent_path"],
        "session": meta.get("id"),
        "parent_session": parent,
        "path": str(target.relative_to(repo)),
        "role": "implementation" if agent not in noncontributors else "noncontributing_attempt",
        "observed_turns": observations,
        "session_meta_line": 1,
        "session_meta_sha256": hashlib.sha256(lines[0]).hexdigest(),
    })
report = repo / "docs/dev/project-management/autopilot/reports/00009-cycle1-rework-worker-evidence.json"
report.write_text(json.dumps(sorted(rows, key=lambda row: row["agent"]), indent=2) + "\n")
print(f"Preserved {len(rows)} native worker sessions")
