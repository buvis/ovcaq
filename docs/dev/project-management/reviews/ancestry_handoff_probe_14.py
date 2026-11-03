"""Observe a real runtime replacement at the ledger-creation boundary."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from ovcaq.workflow import _files
from ovcaq.workflow.records import record_defer


def identity(path: Path) -> list[int]:
    info = path.stat()
    return [info.st_dev, info.st_ino]


def probe(replay: bool) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="ovcaq-r14-handoff-", dir="/private/tmp") as folder:
        project = Path(folder)
        parent = project / "ancestor"
        runtime = parent / "runtime"
        deferred = runtime / "deferred"
        displaced = project / "displaced"
        runtime.mkdir(parents=True)
        record = {"op_id": "handoff-probe"}
        seed = None
        if replay:
            seed = record_defer(runtime, "00004-a.md", "batch", record).read_bytes()
        real_mkdir = os.mkdir
        real_fsync = os.fsync
        observations: list[dict[str, object]] = []
        replaced = False
        before = identity(runtime)
        parent_identity = identity(parent)

        def observe_fsync(descriptor: int) -> None:
            info = os.fstat(descriptor)
            real_fsync(descriptor)
            observations.append({"event": "fsync", "identity": [info.st_dev, info.st_ino]})

        def interleave_mkdir(path: str | bytes | os.PathLike[str], mode: int = 0o777, *, dir_fd: int | None = None) -> None:
            nonlocal replaced
            if Path(os.fsdecode(path)) == deferred and not replaced:
                runtime.rename(displaced)
                real_mkdir(runtime)
                replaced = True
                observations.append({
                    "event": "replace", "old": before,
                    "displaced": identity(displaced), "new": identity(runtime),
                    "boundary": "after-chain-before-deferred-mkdir",
                })
            real_mkdir(path, mode, dir_fd=dir_fd)

        with patch.object(os, "mkdir", interleave_mkdir), patch.object(os, "fsync", observe_fsync):
            try:
                result = record_defer(runtime, "00004-a.md", "batch", record)
                status, error = "success", None
            except Exception as caught:
                result = None
                status, error = "refused", repr(caught)
        index = next((i for i, row in enumerate(observations) if row["event"] == "replace"), None)
        after = observations[index + 1:] if index is not None else []
        old_ledger = displaced / "deferred/batch-deferred.json"
        return {
            "replay": replay, "module": _files.__file__,
            "module_sha256": hashlib.sha256(Path(_files.__file__).read_bytes()).hexdigest(),
            "status": status, "error": error, "replacement_happened": replaced,
            "parent_identity": parent_identity,
            "parent_confirmed_before_replacement": any(row.get("identity") == parent_identity for row in observations[:index]),
            "parent_confirmed_after_replacement": any(row.get("identity") == parent_identity for row in after),
            "returned_path_exists": result.exists() if result else None,
            "ledger": json.loads(result.read_text()) if result else None,
            "displaced_seed_preserved": old_ledger.read_bytes() == seed if seed is not None else not old_ledger.exists(),
            "events": observations,
            "limit": "Real rename/recreation and actual fsync calls; syscall-order evidence only, no physical power-loss simulation.",
        }


if __name__ == "__main__":
    print(json.dumps([probe(False), probe(True)], indent=2))
