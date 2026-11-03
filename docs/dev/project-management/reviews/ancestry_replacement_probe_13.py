"""Reproduce replacement between ancestry confirmation steps without repo edits."""

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from ovcaq.workflow import _files


def probe() -> dict:
    with tempfile.TemporaryDirectory(prefix="ovcaq-r13-ancestry-", dir="/private/tmp") as folder:
        project = Path(folder)
        ancestor = project / "ancestor"
        runtime = ancestor / "runtime"
        moved = project / "displaced"
        ancestor.mkdir()
        original_open = _files._open_lifecycle_directory
        original_fsync = os.fsync
        observations = []
        opened_count = 0
        replaced = False

        def identity(path: Path) -> list[int]:
            value = path.stat()
            return [value.st_dev, value.st_ino]

        def observe_fsync(descriptor: int) -> None:
            value = os.fstat(descriptor)
            observations.append({"event": "fsync", "identity": [value.st_dev, value.st_ino]})
            original_fsync(descriptor)

        @contextmanager
        def interleave(directory: Path, **kwargs):
            nonlocal opened_count, replaced
            if directory == ancestor:
                opened_count += 1
                if opened_count == 2:
                    ancestor.rename(moved)
                    ancestor.mkdir()
                    replaced = True
                    observations.append({"event": "replace", "new": identity(ancestor), "old": identity(moved)})
            with original_open(directory, **kwargs) as descriptor:
                yield descriptor

        project_identity = identity(project)
        with patch.object(_files, "_open_lifecycle_directory", interleave), patch.object(os, "fsync", observe_fsync):
            try:
                result = _files.record_defer(runtime, "00004-a.md", "batch", {"op_id": "replacement-probe"})
                status = "success"
                error = None
            except Exception as caught:
                result = None
                status = "refused"
                error = repr(caught)

        replacement_index = next((i for i, row in enumerate(observations) if row["event"] == "replace"), None)
        after = observations[replacement_index + 1:] if replacement_index is not None else []
        return {
            "module": _files.__file__,
            "status": status,
            "error": error,
            "replacement_happened": replaced,
            "project_identity": project_identity,
            "parent_confirmed_after_replacement": any(row.get("identity") == project_identity for row in after),
            "returned_path_exists": result.exists() if result else None,
            "ledger": json.loads(result.read_text()) if result else None,
            "events": observations,
            "limit": "Real directory rename/recreation and fsync observation; no simulated physical power-loss claim.",
        }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2))
