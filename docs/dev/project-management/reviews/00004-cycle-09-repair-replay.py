"""Replay the 56 retained behavioral regressions against the R8 repair base."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

BASE = "8ef6c0d8ab111c33cd0b49ac50e71fb79a9512a7"
TESTS = [
    "tests/workflow/test_saga_artifacts.py",
    "tests/workflow/test_ledger_integrity.py",
    "tests/workflow/test_report_recovery.py",
    "tests/workflow/test_blank_decisions.py",
    "tests/packaging/test_input_integrity.py",
]


def command(argv: list[str], root: Path, timeout: int = 180):
    return subprocess.run(argv, cwd=root, capture_output=True, text=True, check=False, timeout=timeout)


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    with tempfile.TemporaryDirectory(prefix="ft04r9-replay-") as temporary:
        worktree = Path(temporary).resolve() / "wt"
        added = command(["git", "worktree", "add", "--detach", str(worktree), BASE], root)
        if added.returncode:
            raise RuntimeError(added.stderr)
        try:
            # Overlay tests/support only; all production code remains at BASE.
            shutil.copytree(root / "tests", worktree / "tests", dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            argv = ["mise", "exec", "--", "uv", "run", "python", "-m", "pytest",
                    "-q", "-rA", "-p", "no:cacheprovider", "--continue-on-collection-errors", *TESTS]
            result = command(argv, worktree)
            print(json.dumps({"base": BASE, "head": command(["git", "rev-parse", "HEAD"], root).stdout.strip(),
                              "command": argv, "tests": TESTS, "exit": result.returncode,
                              "stdout": result.stdout, "stderr": result.stderr,
                              "production_diff": command(["git", "diff", "--", "src"], worktree).stdout}, indent=2))
        finally:
            removed = command(["git", "worktree", "remove", "--force", str(worktree)], root)
            if removed.returncode:
                raise RuntimeError(removed.stderr)


if __name__ == "__main__":
    main()
