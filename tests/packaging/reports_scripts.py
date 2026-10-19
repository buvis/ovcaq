"""Programs executed by the isolated installed interpreter in boundary tests."""

COMPLETED_SUMMARY = """
import sys
from pathlib import Path
from unittest.mock import patch
from ovcaq.cli import main
from ovcaq.paths import state_path
from ovcaq.state.store import StateStore
root = Path(sys.argv[1])
rich = dict(filename="00003-rich.md", cycles=2, autonomous_decisions=4,
            escalated_decisions=1, tasks_completed=12, tasks_total=12)
legacy = dict(filename="00001-legacy.md")
rows = {
    "empty": [], "rich": [rich], "legacy": [legacy], "mixed": [rich, legacy],
    "legacy-name": [legacy["filename"]], "mixed-name": [rich, legacy["filename"]],
}[sys.argv[2]]
store = StateStore(state_path(root))
argv = ["--root", str(root), "--json", "workflow", "render", "report"]
if sys.argv[2] in {"empty", "rich"}:
    store.transaction(lambda state: state["batch"].update({"completed_prds": rows}))
    sys.exit(main(argv))
# TEST-062 is a tolerant projection contract; legacy rows cannot enter strict v1 state.
projection = store.read()
projection["batch"]["completed_prds"] = rows
with patch.object(StateStore, "read", autospec=True, return_value=projection):
    sys.exit(main(argv))
"""


SET_BATCH = """
import sys
from pathlib import Path
from ovcaq.paths import state_path
from ovcaq.state.store import StateStore
root = Path(sys.argv[1])
batch_id = sys.argv[2]
StateStore(state_path(root)).transaction(
    lambda state: state["batch"].update({
        "id": batch_id,
        "status": "running",
        "started_at": "2026-09-02T10:00:00Z",
    })
)
"""


POISON_PRD = """
import sys
from pathlib import Path
from ovcaq.paths import state_path
from ovcaq.state.store import StateStore
root = Path(sys.argv[1])
StateStore(state_path(root)).transaction(
    lambda state: state["work"].update({"prd": "00004-safe\\n## Injected.md"})
)
"""


UPDATE_REPORT_STATE = """
import sys
from pathlib import Path
from ovcaq.paths import state_path
from ovcaq.state.store import StateStore
root = Path(sys.argv[1])
def update(state):
    state["work"].update(
        prd=sys.argv[2], phase=sys.argv[3], next_phase=sys.argv[4], tasks_completed=1,
    )
    state["tasks"][0]["status"] = "completed"
    state["batch"]["completed_prds"] = [dict(
        filename="00003-earlier.md", cycles=int(sys.argv[5]),
        autonomous_decisions=4, escalated_decisions=1,
        tasks_completed=2, tasks_total=2,
    )]
StateStore(state_path(root)).transaction(update)
"""
