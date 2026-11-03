"""Retain fresh original-harness results and independent installed lock probes."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

from ovcaq.state.schema import new_state
from ovcaq.state.store import StateStore
from ovcaq.workflow import _files, records

ROOT = Path.cwd()
REV = ROOT / "dev/local/reviews"


def save(name, value):
    (REV / f"00004-cycle-10-{name}.json").write_text(json.dumps(value, indent=2) + "\n")


def invoke(argv, **kwargs):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=40, check=False, **kwargs)
    return {"argv": argv, "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def original_harnesses():
    summary = []
    for name in ("probes", "publication-probes", "adjudication-probes"):
        result = invoke([sys.executable, str(REV / f"00004-cycle-09-{name}.py")])
        save("original-" + name, result)
        summary.append({"harness": name, "exit": result["exit"]})
    path = REV / "00004-cycle-09-adjudication-probes.py"
    spec = importlib.util.spec_from_file_location("cycle09", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    save("adjudication-supplement", [module.frontmatter_policy("skip", None), module.frontmatter_policy("force", "2026-09-05T10:00:00Z"), module.missing_source()])
    return summary


def installed_checks():
    with tempfile.TemporaryDirectory(prefix="ft04r10-installed-") as temporary:
        sandbox = Path(temporary).resolve()
        project = sandbox / "project"
        project.mkdir()
        envroot = sandbox / "env"
        environment = {**os.environ, "XDG_CONFIG_HOME": str(sandbox / "xdg"), "PYTHONNOUSERSITE": "1"}
        for key in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"):
            environment.pop(key, None)
        for argv in (["uv", "venv", "--python", sys.executable, str(envroot)], ["uv", "pip", "install", "--python", str(envroot / "bin/python"), "--no-deps", str(ROOT / "dist/ovcaq-0.1.0.dev0-py3-none-any.whl")]):
            result = invoke(argv, env=environment)
            assert result["exit"] == 0, result
        origin = invoke([str(envroot / "bin/python"), "-c", "import ovcaq,ovcaq.config; print(ovcaq.__file__); print(ovcaq.config.__file__)"], cwd=project, env=environment)
        assert origin["exit"] == 0 and "site-packages" in origin["stdout"] and str(ROOT / "src") not in origin["stdout"]
        runtime = project / "runtime"
        runtime.mkdir()
        state = new_state(repo_root=project)
        state["batch"].update(id="batch", status="running", started_at="2026-09-05T20:00:00Z")
        state["work"]["prd"] = "00004.md"
        store = StateStore(runtime / "state.json")
        store.initialize(state)
        before = store.path.read_bytes()
        record = project / "record.json"
        record.write_text('{"op_id": "second"}')
        argv = [str(envroot / "bin/ovcaq"), "--root", str(project), "--json", "workflow", "defer", "--runtime-root", str(runtime), "--prd", "00004.md", "--record", str(record)]
        path = records.record_defer(runtime, "00004.md", "batch", {"op_id": "seed"})
        native_replace = os.replace
        rivals = []

        def replace(source, destination, **kwargs):
            if destination == path.name and not rivals:
                lock = path.with_suffix(".json.lock")
                lock.rename(lock.with_suffix(".retained"))
                rivals.append(invoke(argv, cwd=project, env=environment))
            native_replace(source, destination, **kwargs)

        with patch.object(_files.os, "replace", replace):
            try:
                records.record_defer(runtime, "00004.md", "batch", {"op_id": "first"})
            except OSError as error:
                original_error = str(error)
            else:
                raise AssertionError("displaced sidecar writer should refuse")
        rival = rivals[0]
        assert rival["exit"] != 0 and rival["stdout"] == "" and "Traceback" not in rival["stderr"], rival
        envelope = json.loads(rival["stderr"])
        assert "deferred publication busy; retry" in envelope["error"]["message"], envelope
        retry = invoke(argv, cwd=project, env=environment)
        assert retry["exit"] == 0, retry
        records.record_defer(runtime, "00004.md", "batch", {"op_id": "first"})
        retained = path.read_bytes()
        assert invoke(argv, cwd=project, env=environment)["exit"] == 0
        assert path.read_bytes() == retained and store.path.read_bytes() == before
        ids = [row["op_id"] for row in records.load_deferred_records(runtime, "batch")]
        assert ids == ["seed", "first", "second"]
        lock_result = {"origin": origin, "original_error": original_error, "rival": rival, "retry": retry, "ids": ids, "exact_replay": True, "state_preserved": True}
        save("installed-lock", lock_result)
        config_rows = []
        for scope in ("project", "user"):
            for field in ("recognized", "ignored"):
                config = project / "ovcaq.toml" if scope == "project" else sandbox / "xdg/ovcaq/config.toml"
                config.parent.mkdir(parents=True, exist_ok=True)
                payload = ("[workflow]\nprd_root = " if field == "recognized" else "ignored = ") + "[" * 2000 + '"prds"' + "]" * 2000 + "\n"
                config.write_text(payload)
                result = invoke([str(envroot / "bin/ovcaq"), "--root", str(project), "--json", "workflow", "select", "--runtime-root", str(runtime)], cwd=project, env=environment)
                assert result["exit"] == 1 and result["stdout"] == "" and "Traceback" not in result["stderr"], result
                error = json.loads(result["stderr"])["error"]
                assert error["code"] == "usage" and str(config) in error["message"]
                assert config.read_text() == payload and store.path.read_bytes() == before
                config_rows.append({"scope": scope, "field": field, **result, "state_preserved": True, "config_preserved": True})
                config.unlink()
        save("installed-config", {"origin": origin, "rows": config_rows})
        return {"lock_ids": ids, "lock_rival_exit": rival["exit"], "config_cases": len(config_rows)}


if __name__ == "__main__":
    print(json.dumps({"original_harnesses": original_harnesses(), "installed": installed_checks()}, indent=2))
