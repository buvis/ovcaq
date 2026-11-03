"""Installed-wheel adjudication of the three fresh review candidates.

Writes only context-managed probe roots. JSON evidence is printed for the
coordinator to preserve with apply_patch. Exit zero confirms observations,
not that the product's expected behavior passes.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import select
import stat
import subprocess
import sys
import tempfile
from unittest.mock import patch


def capture(argv: list[str], *, cwd: Path, env: dict[str, str]) -> dict:
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                            text=True, timeout=30, check=False)
    return {"argv": argv, "exit": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def initialize(project: Path, state_path: Path, prd: str) -> object:
    from ovcaq.state.schema import new_state
    from ovcaq.state.store import StateStore
    project.mkdir(parents=True, exist_ok=True)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    value = new_state(repo_root=project)
    value["batch"].update(id="batch", status="running",
                          started_at="2026-09-05T20:00:00Z")
    value["work"]["prd"] = prd
    store = StateStore(state_path)
    store.initialize(value)
    return store


def depth_probe(root: Path, cli: str, env: dict[str, str]) -> list[dict]:
    from ovcaq.workflow.records import load_deferred_records
    observations = []
    for depth in (30, 31, 32, 33):
        project = root / f"depth-{depth}"
        runtime = project / "runtime"
        store = initialize(project, runtime / "state.json", "00004-a.md")
        before = store.path.read_bytes()
        payload = 0
        for _ in range(depth - 1):
            payload = {"child": payload}
        record = {"op_id": "nested", "payload": payload}
        record_path = project / "record.json"
        record_path.write_text(json.dumps(record))
        args = [cli, "--root", str(project), "--json", "workflow", "defer",
                "--runtime-root", str(runtime), "--state", str(store.path),
                "--prd", "00004-a.md", "--record", str(record_path)]
        seed_path = project / "seed.json"
        seed_path.write_text(json.dumps({"op_id": "seed", "detail": "retained"}))
        seeded = capture(args[:-1] + [str(seed_path)], cwd=project, env=env)
        assert seeded["exit"] == 0, seeded
        ledger = runtime / "deferred/batch-deferred.json"
        seed_bytes = ledger.read_bytes()
        appended = capture(args, cwd=project, env=env)
        after = ledger.read_bytes()
        try:
            loaded = {"ids": [row["op_id"] for row in load_deferred_records(runtime, "batch")]}
        except Exception as error:
            loaded = {"error_type": type(error).__name__, "detail": str(error)}
        replay = capture(args, cwd=project, env=env)
        subsequent = capture(args[:-1] + [str(seed_path)], cwd=project, env=env)
        observations.append({"record_depth": depth, "seed": seeded,
                             "append": appended, "load": loaded,
                             "replay": replay, "subsequent": subsequent,
                             "ledger_text": after.decode(),
                             "seed_bytes_preserved": after == seed_bytes,
                             "state_unchanged": store.path.read_bytes() == before})
    assert observations[0]["append"]["exit"] == 0
    assert observations[0]["load"]["ids"] == ["seed", "nested"]
    for observation in observations[1:3]:
        assert observation["append"]["exit"] == 0
        assert observation["load"]["error_type"] == "ResourceLimitError"
        assert observation["replay"]["exit"] != 0
        assert observation["subsequent"]["exit"] != 0
    assert observations[3]["append"]["exit"] != 0
    assert observations[3]["seed_bytes_preserved"]
    assert all(row["state_unchanged"] for row in observations)
    return observations


def actor(project: Path) -> int:
    from ovcaq.cli import main
    from ovcaq.workflow import reports
    original = reports._publish_file

    def pause_before_publish(*args, **kwargs):
        print("READY", flush=True)
        assert sys.stdin.readline() == "continue\n"
        return original(*args, **kwargs)

    with patch.object(reports, "_publish_file", pause_before_publish):
        return main(["--root", str(project), "--json", "workflow", "render", "report"])


def report_probe(root: Path, cli: str, env: dict[str, str]) -> dict:
    project = root / "report"
    runtime = project / "dev/local/ovcaq"
    store = initialize(project, runtime / "state.json", "00003-seed.md")
    args = [cli, "--root", str(project), "--json", "workflow", "render", "report"]
    seed = capture(args, cwd=project, env=env)
    assert seed["exit"] == 0, seed
    store.transaction(lambda state: state["work"].update(prd="00004-a.md"))
    process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                                "--report-actor", str(project)], cwd=project,
                               env=env, text=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert select.select([process.stdout], [], [], 10)[0], "actor not ready"
        assert process.stdout.readline() == "READY\n"
        store.transaction(lambda state: state["work"].update(prd="00005-b.md"))
        before = store.path.read_bytes()
        second = capture(args, cwd=project, env=env)
        published_b = json.loads(second["stdout"])
        path = Path(published_b["path"])
        b_text = path.read_text()
        stdout, stderr = process.communicate("continue\n", timeout=20)
        a = {"exit": process.returncode, "stdout": stdout, "stderr": stderr}
        final_text = path.read_text()
        state_unchanged = store.path.read_bytes() == before
        retry = capture(args, cwd=project, env=env)
        retry_text = path.read_text()
        result = {"seed": seed, "publisher_a": a, "publisher_b": second,
                  "b_published_text": b_text, "final_text": final_text,
                  "b_section_lost": "## 00005-b.md" in b_text and "## 00005-b.md" not in final_text,
                  "seed_survives": "## 00003-seed.md" in final_text,
                  "a_text_equals_final": json.loads(stdout)["text"] == final_text,
                  "retry_b": retry, "retry_text": retry_text,
                  "retry_retains_a_and_b": all(f"## {prd}" in retry_text for prd in ("00004-a.md", "00005-b.md")),
                  "state_unchanged_by_render": state_unchanged and store.path.read_bytes() == before}
        assert a["exit"] == second["exit"] == retry["exit"] == 0, result
        assert result["b_section_lost"] and result["seed_survives"]
        assert result["a_text_equals_final"] and result["state_unchanged_by_render"]
        assert result["retry_retains_a_and_b"]
        return result
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=10)


def fsync_probe(root: Path) -> dict:
    from ovcaq.cli import main
    from ovcaq.workflow.records import load_deferred_records
    from contextlib import redirect_stdout, redirect_stderr
    import io
    project = root / "fsync"
    runtime = project / "new/nested"
    store = initialize(project, project / "separate/state.json", "00004-a.md")
    before = store.path.read_bytes()
    record = project / "record.json"
    record.write_text(json.dumps({"op_id": "one"}))
    expected = [project, project / "new", runtime, runtime / "deferred"]
    original = os.fsync
    observed = []

    def record_sync(descriptor: int) -> None:
        opened = os.fstat(descriptor)
        if stat.S_ISDIR(opened.st_mode):
            matches = [str(path.relative_to(project)) for path in expected
                       if path.exists() and (path.stat().st_dev, path.stat().st_ino)
                       == (opened.st_dev, opened.st_ino)]
            observed.extend(matches or ["other-directory"])
        original(descriptor)

    args = ["--root", str(project), "--json", "workflow", "defer",
            "--runtime-root", str(runtime), "--state", str(store.path),
            "--prd", "00004-a.md", "--record", str(record)]
    outputs = []
    for _ in range(2):
        observed.clear()
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(os, "fsync", record_sync), redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(args)
        outputs.append({"exit": code, "stdout": stdout.getvalue(), "stderr": stderr.getvalue(),
                        "directory_fsyncs": list(observed),
                        "missing_parent_fsyncs": [str(path.relative_to(project)) for path in expected
                                                  if str(path.relative_to(project)) not in observed]})
    result = {"invocations": outputs, "expected_directory_fsyncs": [str(path.relative_to(project)) for path in expected],
              "ledger_ids": [row["op_id"] for row in load_deferred_records(runtime, "batch")],
              "state_unchanged": before == store.path.read_bytes()}
    assert all(row["exit"] == 0 and row["missing_parent_fsyncs"] == [".", "new"] for row in outputs)
    assert result["ledger_ids"] == ["one"] and result["state_unchanged"]
    return result


def installed(root: Path) -> None:
    import ovcaq
    from ovcaq import cli, workflow_cli
    from ovcaq.workflow import _files, records, reports
    origins = {module.__name__: module.__file__ for module in (ovcaq, cli, workflow_cli, _files, records, reports)}
    assert all("site-packages" in origin for origin in origins.values()), origins
    env = dict(os.environ)
    executable = str(Path(sys.executable).with_name("ovcaq"))
    print(json.dumps({"origins": origins, "depth": depth_probe(root, executable, env),
                      "report": report_probe(root, executable, env), "fsync": fsync_probe(root)}, indent=2))


def launch() -> None:
    wheel = Path.cwd() / "dist/ovcaq-0.1.0.dev0-py3-none-any.whl"
    with tempfile.TemporaryDirectory(prefix="ft04r11-installed-") as temporary:
        root = Path(temporary).resolve()
        environment = {**os.environ, "XDG_CONFIG_HOME": str(root / "xdg"), "PYTHONNOUSERSITE": "1"}
        for key in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"):
            environment.pop(key, None)
        python = root / "env/bin/python"
        for args in (["uv", "venv", "--python", sys.executable, str(root / "env")],
                     ["uv", "pip", "install", "--python", str(python), "--no-deps", str(wheel)]):
            result = capture(args, cwd=root, env=environment)
            assert result["exit"] == 0, result
        result = capture([str(python), str(Path(__file__).resolve()), "--installed", str(root)], cwd=root, env=environment)
        print(json.dumps(result, indent=2))
        assert result["exit"] == 0, result


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--installed":
        installed(Path(sys.argv[2]))
    elif len(sys.argv) > 1 and sys.argv[1] == "--report-actor":
        raise SystemExit(actor(Path(sys.argv[2])))
    else:
        launch()
