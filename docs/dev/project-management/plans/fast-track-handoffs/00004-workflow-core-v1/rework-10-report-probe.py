"""Rerun the R10 installed comparison and require repaired report equality."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from ovcaq.state.schema import new_state
from ovcaq.state.store import StateStore

ROOT = Path.cwd()


def run(argv, **kwargs):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=30, check=False, **kwargs)
    assert result.returncode == 0, result.stderr
    return result.stdout


with tempfile.TemporaryDirectory(prefix="ft04f10-report-") as name:
    sandbox = Path(name).resolve()
    project = sandbox / "project"
    project.mkdir()
    envroot = sandbox / "env"
    environment = {**os.environ, "XDG_CONFIG_HOME": str(sandbox / "xdg"), "PYTHONNOUSERSITE": "1"}
    for key in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"):
        environment.pop(key, None)
    run(["uv", "venv", "--python", sys.executable, str(envroot)], env=environment)
    run(["uv", "pip", "install", "--python", str(envroot / "bin/python"), "--no-deps", str(ROOT / "dist/ovcaq-0.1.0.dev0-py3-none-any.whl")], env=environment)
    origins = run([str(envroot / "bin/python"), "-c", "import ovcaq,ovcaq.workflow_cli,ovcaq.workflow.reports; print(ovcaq.__file__); print(ovcaq.workflow_cli.__file__); print(ovcaq.workflow.reports.__file__)"], cwd=project, env=environment).splitlines()
    assert all("site-packages" in path for path in origins)
    runtime = project / "dev/local/ovcaq"
    runtime.mkdir(parents=True)
    state = new_state(repo_root=project)
    state["batch"].update(id="batch", status="running", started_at="2026-09-05T20:00:00Z")
    state["work"]["prd"] = "00004-first.md"
    store = StateStore(runtime / "state.json")
    store.initialize(state)
    argv = [str(envroot / "bin/ovcaq"), "--root", str(project), "--json", "workflow", "render", "report"]
    first = json.loads(run(argv, cwd=project, env=environment))
    first_file = Path(first["path"]).read_text()
    assert first["text"] == first_file
    store.transaction(lambda current: current["work"].update(prd="00005-second.md"))
    before = store.path.read_bytes()
    second = json.loads(run(argv, cwd=project, env=environment))
    published = Path(second["path"]).read_text()
    third = json.loads(run(argv, cwd=project, env=environment))
    result = {
        "origin": origins, "argv": argv, "exit": 0,
        "first_text_matches_file": first["text"] == first_file,
        "second_text_matches_file": second["text"] == published,
        "first_prd_in_json_text": "## 00004-first.md" in second["text"],
        "first_prd_in_published_file": "## 00004-first.md" in published,
        "second_prd_in_both": all("## 00005-second.md" in text for text in (second["text"], published)),
        "rerender_json_stable": second == third,
        "rerender_file_stable": Path(second["path"]).read_text() == published,
        "state_unchanged_by_render": store.path.read_bytes() == before,
        "json_text": second["text"], "published_text": published,
    }
    (ROOT / "dev/local/plans/fast-track-handoffs/00004-workflow-core-v1/rework-10-report-probe.json").write_text(json.dumps(result, indent=2) + "\n")
    assert all(value for key, value in result.items() if isinstance(value, bool)), result
    print(json.dumps({key: value for key, value in result.items() if key not in {"json_text", "published_text", "argv", "origin"}}, indent=2))
