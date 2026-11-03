"""Review-only replay preserving current test instrumentation against old production."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path("/Users/bob/git/src/github.com/buvis/ovcaq")
BASE = "7b41798c80e06a2c341d75116a09c752203797f4"
HEAD = "4011d1a3ce186ae9dcd023e8a7fb4b87412b935d"
OVERLAY = [
    "tests/packaging/test_rework_13.py",
    "tests/packaging/rework_13_scripts.py",
]
NODE = "tests/packaging/test_rework_13.py::test_installed_defer_never_succeeds_through_unconfirmed_reparented_ancestry"

def run(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=300, check=False)

with tempfile.TemporaryDirectory(prefix="ovcaq-r16-replay-") as temporary:
    worktree = Path(temporary).resolve() / "worktree"
    added = run(["git", "worktree", "add", "--detach", str(worktree), BASE], ROOT)
    if added.returncode:
        raise RuntimeError(added.stderr)
    try:
        overlaid = run(["git", "checkout", HEAD, "--", *OVERLAY], worktree)
        if overlaid.returncode:
            raise RuntimeError(overlaid.stderr)
        result = run(["mise", "exec", "--", "uv", "run", "pytest", "-q", "-rA", NODE], worktree)
        evidence = {
            "base": BASE, "head": HEAD, "overlay": OVERLAY,
            "purpose": "Current actor plus test against old production; confirm failure is behavioral, not missing actor mode",
            "command": "mise exec -- uv run pytest -q -rA " + NODE,
            "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
        }
    finally:
        removed = run(["git", "worktree", "remove", "--force", str(worktree)], ROOT)
        if removed.returncode:
            raise RuntimeError(removed.stderr)
(ROOT / "dev/local/reviews/00004-cycle-16-instrumented-replay.json").write_text(json.dumps(evidence, indent=2) + "\n")
print(result.stdout)
print("exit:", result.returncode)

