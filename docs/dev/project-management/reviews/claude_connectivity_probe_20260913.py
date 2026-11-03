"""Bounded connectivity evidence; never emits reviewer verdicts or a receipt."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import uuid
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path.home() / ".config/autocodex"))
import driver  # noqa: E402


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    state = root / "dev/local/autopilot/state.json"
    before = hashlib.sha256(state.read_bytes()).hexdigest()
    stem = Path(__file__).with_name(f"claude-connectivity-{uuid.uuid4().hex}")
    result = driver.run_process(
        driver.claude_argv("claude", "opus"),
        "Connectivity probe only. Do not use tools, inspect files, review code, "
        "or change anything. Reply with exactly AUTOCODEX_CONNECTIVITY_OK.",
        root,
        driver.reviewer_env(dict(os.environ)),
        stem,
        60,
        provider="claude",
    )
    rows = [json.loads(line) for line in result.log.read_text().splitlines()]
    terminal = next(row for row in reversed(rows) if row.get("type") == "result")
    summary = {
        "purpose": "connectivity only; not a review",
        "ok": result.ok,
        "response": result.events.text,
        "raw": str(result.log),
        "usage": result.events.usage,
        "models": list(terminal.get("modelUsage", {})),
        "state_unchanged": before == hashlib.sha256(state.read_bytes()).hexdigest(),
        "receipt_created": False,
    }
    stem.with_suffix(".summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if result.ok and summary["state_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
