"""FT-04R9 coordinator probes; all effects are confined to temporary fixtures."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from ovcaq.workflow import _files, records


def previous_probes():
    path = Path(__file__).with_name("00004-cycle-08-probes.py")
    spec = importlib.util.spec_from_file_location("ft04r8_probes", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lock_replacement(at_syscall: bool) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="ft04r9-lock-") as temporary:
        root = Path(temporary).resolve()
        replaced = False
        competitor_success = False
        native_replace = os.replace

        def compete() -> None:
            nonlocal replaced, competitor_success
            replaced = True
            lock = root / "deferred/batch-deferred.json.lock"
            lock.rename(lock.with_suffix(".retained"))
            records.record_defer(root, "00004.md", "batch", {"op_id": "second"})
            competitor_success = True

        def replace(*args, **kwargs) -> None:
            if at_syscall and not replaced and args[1] == "batch-deferred.json":
                compete()
            native_replace(*args, **kwargs)

        def boundary(reached: records.DeferBoundary) -> None:
            if not at_syscall and reached is records.DeferBoundary.BEFORE_PUBLISH:
                compete()

        error = None
        with patch.object(_files.os, "replace", replace):
            try:
                records.record_defer(root, "00004.md", "batch", {"op_id": "first"}, boundary_hook=boundary)
            except OSError as exc:
                error = str(exc)
        before = [r["op_id"] for r in records.load_deferred_records(root, "batch")]
        records.record_defer(root, "00004.md", "batch", {"op_id": "first"})
        after = [r["op_id"] for r in records.load_deferred_records(root, "batch")]
        return {"case": "lock-at-replace" if at_syscall else "lock-at-before-publish", "error": error,
                "competitor_success": competitor_success, "before_retry": before, "after_retry": after}


def nested_configuration() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="ft04r9-config-") as temporary:
        root = Path(temporary).resolve()
        config = root / "ovcaq.toml"
        payload = "[workflow]\nprd_root = " + "[" * 2000 + '"prds"' + "]" * 2000 + "\n"
        config.write_text(payload)
        result = subprocess.run(
            [sys.executable, "-m", "ovcaq", "--root", str(root), "--json", "workflow", "select"],
            env={**os.environ, "XDG_CONFIG_HOME": str(root / "xdg")},
            capture_output=True, text=True, timeout=5, check=False,
        )
        return {"case": "nested-workflow-config", "exit": result.returncode,
                "stdout": result.stdout, "traceback": "Traceback" in result.stderr,
                "stderr_tail": result.stderr.splitlines()[-4:], "config_preserved": config.read_text() == payload}


def main() -> None:
    old = previous_probes()
    observations = [old.run(kind, replacement) for kind in ("stall", "park")
                    for replacement in ("source-before-rename", "held-after-rename", "held-across-restart")]
    observations.extend((lock_replacement(False), lock_replacement(True), old.report_other_prd()))
    observations.extend(old.corrupt_ledger())
    observations.extend((old.deep_ledger_cli(), old.blank_decision()))
    observations.extend(old.fifo_inputs())
    observations.extend(old.report_durability())
    observations.append(nested_configuration())
    print(json.dumps(observations, indent=2))


if __name__ == "__main__":
    main()
