"""Installed-wheel check for the relative-depth gap found by Devon round 2."""

import argparse
import json
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests/packaging"))
from packaging_support import InstalledWheel, isolated_environment
from test_rework_13 import (
    _assert_one_record,
    _assert_replaced_after_confirmation,
    _identity,
    _invoke,
    _ledger,
    _prepare,
    _state_bytes,
)


def check(installed, folder, distance, replay, expect_success):
    project = _prepare(installed, folder)
    ancestor = project / uuid4().hex
    ancestor.mkdir()
    runtime = ancestor.joinpath(*(uuid4().hex for _ in range(distance)))
    before = _state_bytes(project)
    old_identity = _identity(ancestor)
    seed = None
    if replay:
        assert _invoke(installed, project, "normal", runtime=runtime, ancestor=ancestor)["exit"] == 0
        seed = _assert_one_record(runtime)
    result = _invoke(installed, project, "replace", runtime=runtime, ancestor=ancestor)
    _assert_replaced_after_confirmation(result, project, ancestor, old_identity)
    assert _state_bytes(project) == before
    displaced_runtime = project / "displaced" / runtime.relative_to(ancestor)
    if replay:
        assert _ledger(displaced_runtime).read_bytes() == seed
    if expect_success:
        assert result["exit"] == 0, result
        _assert_one_record(runtime)
    else:
        assert result["exit"] == 2 and result["os_error"] is True, result
        assert "identity changed; retry" in result["error"], result
        assert str(ancestor) in result["error"], result
        assert not _ledger(runtime).exists()
        retry = _invoke(installed, project, "normal", runtime=runtime, ancestor=ancestor)
        assert retry["exit"] == 0, retry
        _assert_one_record(runtime)
        assert _state_bytes(project) == before
    return {
        "distance_from_runtime": distance, "replay": replay,
        "exit": result["exit"], "error": result.get("error"),
        "chronology_verified": True, "state_and_backup_unchanged": True,
        "displaced_ledger_preserved": replay, "fresh_retry_verified": not expect_success,
        "origins": result["origins"],
    }


parser = argparse.ArgumentParser()
parser.add_argument("installed_root", type=Path)
parser.add_argument("--expect-success", action="store_true")
args = parser.parse_args()
with tempfile.TemporaryDirectory(prefix="ovcaq-r13-distant-", dir=ROOT / "dev/local/tmp") as temp:
    folder = Path(temp)
    installed = InstalledWheel(
        args.installed_root, args.installed_root / "bin/python",
        args.installed_root / "bin/ovcaq", isolated_environment(folder / "environment"),
    )
    results = []
    for distance in (3, 5):
        for replay in (False, True):
            case = folder / f"case-{distance}-{replay}"
            case.mkdir()
            results.append(check(installed, case, distance, replay, args.expect_success))
    print(json.dumps({"expected_baseline_success": args.expect_success, "results": results}, indent=2))
