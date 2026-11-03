"""Review-only synthetic proof of a fleet-record replacement during remove."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ovcaq.runtime.registry import FleetEntry, FleetRegistry, process_identity


def main() -> None:
    identity = process_identity(os.getpid())
    assert identity is not None
    with TemporaryDirectory(prefix="ovcaq-review-fleet-") as temporary:
        root = Path(temporary).resolve()
        registry = FleetRegistry(root / "runs")
        old = FleetEntry(1, root, identity.pid, identity.started, "run", "old", "2026-09-25T20:00:00Z")
        new = FleetEntry(1, root, identity.pid, identity.started, "run", "new", "2026-09-25T21:00:00Z")
        destination = registry.publish(old)
        replacement_registry = FleetRegistry(root / "replacement")
        replacement = replacement_registry.publish(new)
        original_unlink = os.unlink
        swapped = False

        def swap_before_unlink(path: str, *, dir_fd: int | None = None) -> None:
            nonlocal swapped
            if path == destination.name and dir_fd is not None and not swapped:
                os.replace(replacement, destination.name, dst_dir_fd=dir_fd)
                swapped = True
            original_unlink(path, dir_fd=dir_fd)

        with patch("os.unlink", side_effect=swap_before_unlink):
            removed = registry.remove("run", expected=old)
        print(json.dumps({
            "replacement_injected": swapped,
            "remove_reported_success": removed,
            "new_live_entry_deleted": not destination.exists(),
            "synthetic_only": True,
        }, sort_keys=True))


if __name__ == "__main__":
    main()

