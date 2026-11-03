"""Review-only reproduction: purge opens one runtime but locks its replacement."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from ovcaq.paths import ensure_runtime_layout, resolve_runtime_paths
from ovcaq.runtime.registry import DuplicateRunError, RunLock
from ovcaq.runtime.session import apply_purge, plan_purge


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="ovcaq-review-purge-") as temporary:
        sandbox = Path(temporary).resolve()
        project = sandbox / "project"
        project.mkdir()
        paths = resolve_runtime_paths(project, xdg_state_home=sandbox / "xdg")
        ensure_runtime_layout(paths)
        selected = paths.sessions / "synthetic-session"
        selected.mkdir(mode=0o700)
        (selected / "raw.jsonl").write_bytes(b"synthetic active evidence\n")
        plan = plan_purge(paths, session_id="synthetic-session")
        moved = paths.runtime_root.with_name("moved-runtime")
        real_open = os.open
        swapped = False

        def swap_after_open(path, flags, mode=0o777, *, dir_fd=None):
            nonlocal swapped
            descriptor = real_open(path, flags, mode, dir_fd=dir_fd)
            if not swapped and dir_fd is None and Path(path) == paths.runtime_root:
                paths.runtime_root.rename(moved)
                paths.runtime_root.mkdir(mode=0o700)
                swapped = True
            return descriptor

        with RunLock.acquire(paths.run_lock):
            with patch("os.open", side_effect=swap_after_open):
                deleted = apply_purge(plan)
            original_lock_held = False
            try:
                with RunLock.acquire(moved / "run.lock"):
                    pass
            except DuplicateRunError:
                original_lock_held = True
            print(json.dumps({
                "runtime_swapped_after_open": swapped,
                "original_run_lock_still_held": original_lock_held,
                "apply_returned_success": bool(deleted),
                "active_evidence_deleted": not (
                    moved / "sessions" / "synthetic-session" / "raw.jsonl"
                ).exists(),
            }, sort_keys=True))


if __name__ == "__main__":
    main()
