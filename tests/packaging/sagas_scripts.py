"""Programs executed by the isolated installed interpreter in boundary tests."""

INTENT_CONFLICT = """
import sys
from pathlib import Path
from ovcaq.paths import state_path
from ovcaq.state.store import StateStore
from ovcaq.workflow.paths import resolve_lifecycle_paths
from ovcaq.workflow.records import SagaBoundary, park, stall
root = Path(sys.argv[1])
def interrupt(boundary):
    if boundary is SagaBoundary.AFTER_INTENT_BEFORE_MOVE:
        raise RuntimeError("interrupted")
kwargs = dict(
    paths=resolve_lifecycle_paths(root, Path("docs/dev/project-management/prds")),
    runtime_root=root / "docs/dev/project-management/ovcaq", boundary_hook=interrupt,
    detail="session ended without a committed transition",
)
try:
    if sys.argv[2] == "kind":
        park(StateStore(state_path(root)), **kwargs)
    else:
        stall(StateStore(state_path(root)), prd="00004-workflow-core-v1.md",
              site="wrapper_died", **kwargs)
except RuntimeError as error:
    assert str(error) == "interrupted"
else:
    raise AssertionError("intent boundary not reached")
"""


REPLACE_DEFERRED = """
import sys
from pathlib import Path
from unittest.mock import patch
from ovcaq.cli import main
from ovcaq.workflow import records
root = Path(sys.argv[1])
command, boundary = sys.argv[2:4]
deferred = root / "docs/dev/project-management/ovcaq/deferred"
def replace(reached):
    if reached.value == boundary:
        deferred.rename(deferred.with_name("relocated"))
        deferred.mkdir()
argv = ["--root", str(root), "--json", "workflow", command]
if command == "defer":
    argv += ["--prd", "00004-workflow-core-v1.md", "--record", str(root / "record.json")]
    target = "ovcaq.workflow.records.record_defer"
    original = records.record_defer
else:
    target = "ovcaq.workflow_cli." + command
    original = getattr(records, command)
    if command == "stall":
        argv += ["--prd", "00004-workflow-core-v1.md", "--site", "gate", "--detail", "later"]
def injected(*args, **kwargs):
    return original(*args, **kwargs, boundary_hook=replace)
with patch(target, autospec=True, side_effect=injected):
    sys.exit(main(argv))
"""


INTERRUPT_STALL = """
import sys
from pathlib import Path
from ovcaq.paths import state_path
from ovcaq.state.store import StateStore
from ovcaq.workflow.paths import resolve_lifecycle_paths
from ovcaq.workflow.records import SagaBoundary, stall

root = Path(sys.argv[1])
store = StateStore(state_path(root))
paths = resolve_lifecycle_paths(root, Path("docs/dev/project-management/prds"))
def interrupt(boundary):
    if boundary is SagaBoundary.AFTER_INTENT_BEFORE_MOVE:
        raise RuntimeError("intent committed")
try:
    stall(
        store,
        paths=paths,
        runtime_root=root / "docs/dev/project-management/ovcaq",
        prd="00004-workflow-core-v1.md",
        site="design_gate",
        detail="approval missing",
        boundary_hook=interrupt,
        operation_id_factory=lambda: "installed-recovery-operation",
        now=lambda: "2026-09-03T10:01:00Z",
    )
except RuntimeError as error:
    if str(error) != "intent committed":
        raise
else:
    raise RuntimeError("saga did not reach the intent boundary")
"""
