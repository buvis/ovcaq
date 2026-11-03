"""Test configured publication identity with disposable report/audit/archive roots."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from ovcaq.state.schema import new_state
from ovcaq.state.store import StateStore
from ovcaq.workflow import reports


def observe(surface: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="ft04r9-publish-") as temporary:
        root = Path(temporary).resolve()
        state = new_state(repo_root=root)
        state["batch"].update(id="review-09", status="running", started_at="2026-09-05T12:00:00Z")
        state["work"].update(prd="00004.md", phase="done", next_phase="")
        store = StateStore(root / "state.json")
        store.initialize(state)
        state = store.read()
        target = root / ("dev/local/reviews" if surface == "audit" else "reports")
        retained = target.with_name(target.name + "-retained")
        replaced = False
        native_replace = os.replace

        def replace(*args, **kwargs) -> None:
            nonlocal replaced
            if not replaced:
                replaced = True
                target.rename(retained)
                target.mkdir()
            native_replace(*args, **kwargs)

        error = None
        result = None
        with patch.object(reports.os, "replace", replace):
            try:
                if surface == "audit":
                    result = reports.publish_audit(root, state)
                elif surface == "archive":
                    result = reports.archive_final_state(root, state)
                else:
                    result = reports.publish_report(root, state, ())
            except OSError as exc:
                error = str(exc)
        return {"surface": surface, "error": error, "returned_success": result is not None,
                "returned_path_exists": result is not None and result.exists(),
                "retained_files": sorted(p.name for p in retained.iterdir()),
                "configured_files": sorted(p.name for p in target.iterdir())}


if __name__ == "__main__":
    print(json.dumps([observe(surface) for surface in ("report", "audit", "archive")], indent=2))
