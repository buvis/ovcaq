"""Complete FT-04R8 test overlay for the installed review replay helper.

Unlike its generic overlay, this includes split helpers and retained fixtures;
pytest collects from tests/ so absent new production modules are collection
errors instead of an initial conftest startup abort. No implementation is edited.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BASE = "b43bf2c94d5eb0fddafca55542ef2570b45e8d52"
REPO = Path(__file__).resolve().parents[3]
HELPERS = Path("/Users/bob/.claude/plugins/cache/buvis-plugins/autopilot/0.5.0/skills/review-work-completion/scripts")


def command(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=root, capture_output=True, text=True, check=False)


def main() -> None:
    sys.path.insert(0, str(HELPERS))
    spec = importlib.util.spec_from_file_location("ft04r8_replay", HELPERS / "replay_tests_against_base.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    changed = command(REPO, "git", "diff", "--name-only", "--diff-filter=d", BASE, "HEAD").stdout.splitlines()
    overlay = [path for path in changed if path.startswith("tests/")]
    touched = {path: module.touched_tests(REPO, BASE, path) for path in overlay if module.is_test_file(Path(path))}
    temporary = Path(tempfile.mkdtemp(prefix="ft04r8-replay-")).resolve()
    worktree = temporary / "worktree"
    try:
        added = command(REPO, "git", "worktree", "add", "--detach", str(worktree), BASE)
        if added.returncode:
            raise RuntimeError(added.stderr)
        head = command(REPO, "git", "rev-parse", "HEAD").stdout.strip()
        copied = command(worktree, "git", "checkout", head, "--", *overlay)
        if copied.returncode:
            raise RuntimeError(copied.stderr)
        result = subprocess.run(["mise", "exec", "--", "uv", "run", "pytest", "tests", "-q", "-rA", "-p", "no:cacheprovider", "--continue-on-collection-errors"],
                                cwd=worktree, capture_output=True, text=True, check=False, timeout=120)
        rows = [dict(outcome=outcome, file=path, test=name) for outcome, path, name in module.parse_results(result.stdout)
                if path in touched and (touched[path] is None or name in touched[path])]
        counts = {name: sum(row["outcome"] == name for row in rows) for name in ("PASSED", "FAILED", "ERROR", "SKIPPED")}
        summary = {"base": BASE, "head": head, "overlay": overlay, "command": "mise exec -- uv run pytest tests -q -rA -p no:cacheprovider --continue-on-collection-errors", "exit": result.returncode,
                   "touched_counts": counts, "uncollectable": sorted(set(module.COLLECT_ERROR_RE.findall(result.stdout))), "touched_results": rows,
                   "runner_output": result.stdout + result.stderr}
        artifact = Path(__file__).with_name("00004-cycle-08-replay-result.json")
        artifact.write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps({"artifact": str(artifact), "exit": result.returncode,
                          "touched_counts": counts, "uncollectable": summary["uncollectable"],
                          "summary": result.stdout.splitlines()[-1:]}, indent=2))
    finally:
        removed = command(REPO, "git", "worktree", "remove", "--force", str(worktree))
        if removed.returncode:
            print(f"cleanup warning: {removed.stderr}", file=sys.stderr)
        shutil.rmtree(temporary)


if __name__ == "__main__":
    main()
