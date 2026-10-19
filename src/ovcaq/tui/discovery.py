"""Project the shared fleet registry for presentation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ovcaq.runtime.registry import FleetRegistry, FleetRun


class MissingRunError(ValueError):
    """No run matches the requested selection."""


@dataclass(frozen=True, slots=True)
class FleetView:
    runs: tuple[FleetRun, ...]
    malformed_entries: tuple[Path, ...]
    stale_entries: tuple[Path, ...]


def discover_fleet(registry: FleetRegistry) -> FleetView:
    """Take one registry snapshot; liveness is the registry's decision."""
    snapshot = registry.snapshot()
    runs = (FleetRun.from_entry(entry) for entry in snapshot.live)
    return FleetView(
        runs=tuple(
            sorted(runs, key=lambda run: (run.root, run.started_at, run.run_id))
        ),
        malformed_entries=snapshot.malformed,
        stale_entries=snapshot.stale,
    )


def select_run(view: FleetView, *, run_id: str | None, root: Path | None) -> FleetRun:
    """Return the single run matching every given selector."""
    matches = [
        run
        for run in view.runs
        if (run_id is None or run.run_id == run_id)
        and (root is None or run.root == root)
    ]
    if len(matches) == 1:
        return matches[0]
    available = ", ".join(f"{run.run_id} ({run.root})" for run in view.runs) or "none"
    problem = "Ambiguous" if matches else "No matching"
    error_type = ValueError if matches else MissingRunError
    raise error_type(f"{problem} run selection; available: {available}")
