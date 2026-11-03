# PRD 00008 recovery task 8

Both production fleet selectors now share sanitized literal rows and show live/stale/malformed counts. Empty plain fleets return without reading input; empty Textual fleets show an empty selector and permit detach without implicitly selecting or launching. Exact selected FleetRun identity remains unchanged.

Micro eligibility computed true for two non-CRITICAL findings in one clean production file. Change: app.py plus CHANGELOG, net16 lines, two files; below ceiling. No Tess/Devon/test commit/red check as mandated by this lane. Style clean, split hygiene skipped:no-tests, self-deslop skipped:trivial. Reflow precommit call was missed; equivalent committed -U0 check found5 app.py hunks and1 CHANGELOG hunk, below20. No formatter sweep. Baseec7857d9c1e1f2a52d08167421d779c3982abaa5; finalf1004f349f08c5752098d54b9ec30fc099c663e6.

Existing narrow suite:12 passed,46 deselected,2 pre-existing pytest cleanup warnings,exit0. Scratch harness exercised real Textual OptionList/Static views and plain selection: C0/C1 removal, literal Rich markup, exact selected object, visible gap counts and safe empty fleets;exit0. No retained test edits. Pat's LOW request for retained regressions is preserved for completion review; the micro lane expressly skips test authoring. Scratch harness is preserved below so this evidence survives temporary-file cleanup.

Patf23eca15: tool-free guarded use-sonnet wrapper with approved network,15,799-byte prompt,session6a373114-3bad-4d24-888f-788b74e0a740,actualclaude-sonnet-5-5. Parser passed; F06/F18 resolved. Per-task review only, fresh completion review remains required. ASSUMPTIONS: none.

## Raw task review

CLOSURE | resolved | F06 Fleet selection renders `run.root` and `run.agent` without `display_text`; configured agents or project paths containing terminal controls can inject output in both Textual and plain modes | `_fleet_row` runs `display_text(str(value))` on run_id, root and agent, and both the `OptionList` rows and `run_plain_fleet` now use it.

CLOSURE | resolved | F18 Malformed and stale registry entries are preserved in `FleetView` but neither the Textual fleet selector nor the plain selector renders them, silently hiding incomplete fleet evidence instead of exposing a telemetry gap | `_fleet_status` prints "N stale, M malformed" and "No live runs available". `FleetApp.compose` yields it as `#fleet-status`, and `run_plain_fleet` prints it first and returns `None` on an empty fleet without reading input.

LOW | src/ovcaq/tui/app.py:237,400 | The diff adds no retained regression test. The only check of the hostile-text and gap behavior is the scratch `docs/dev/tmp/verify_r8.py`, and the 12 recorded `-k fleet` tests passed with or without this change. `rules/testing.md` requires every new behavior and bug fix to ship a test. | Move the scratch assertions into `tests/tui/test_app.py` as named tests, for example `fleet_selectors_strip_controls_from_row` and `fleet_selectors_show_registry_gap_counts`.


## Verification evidence and scratch harness

{
  "command": [
    "uv",
    "run",
    "pytest",
    "-q",
    "--tb=line",
    "tests/tui/test_app.py",
    "-k",
    "fleet"
  ],
  "exit": 0,
  "timeout_seconds": 300
}
............                                                             [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-ab9494ff-37c1-4fbd-8a6b-c86b2f66c279
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-ab9494ff-37c1-4fbd-8a6b-c86b2f66c279'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-89dd5a0d-5198-4bfc-92d0-0c7ef2d10b3e
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-89dd5a0d-5198-4bfc-92d0-0c7ef2d10b3e'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
12 passed, 46 deselected, 2 warnings in 1.84s

{
  "command": [
    "uv",
    "run",
    "python",
    "docs/dev/tmp/verify_r8.py"
  ],
  "exit": 0,
  "timeout_seconds": 300
}
Actual Textual/plain selectors: hostile text literal and control-free, gaps visible, exact identity selected, empty fleet safe

Scratch harness exercising actual selectors; no retained test edits (micro lane):
import asyncio
import io
import os
import tempfile
from pathlib import Path
from rich.text import Text
from textual.widgets import OptionList, Static
from ovcaq.runtime.registry import FleetRun
from ovcaq.tui.app import FleetApp, run_plain_fleet
from ovcaq.tui.discovery import FleetView


async def main():
    with tempfile.TemporaryDirectory() as directory:
        os.environ['XDG_CONFIG_HOME'] = directory
        run = FleetRun('[red]id\x1b\x07\r\x85', Path('/tmp/[bold]root\x1b\n'),
                       '[blue]agent\x9d\x07', '2026-10-03T12:00:00Z', 123, 'start')
        view = FleetView((run,), (Path('bad'), Path('bad2')), (Path('stale'),))
        output = io.StringIO()
        assert run_plain_fleet(view, input_stream=io.StringIO('unknown\n'), output_stream=output) is None
        row = '[red]id  /tmp/[bold]root  [blue]agent'
        text = output.getvalue()
        assert row in text and '1 stale, 2 malformed' in text
        assert not any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in text.replace('\n',''))
        app = FleetApp(view)
        async with app.run_test() as pilot:
            prompt = app.query_one(OptionList).get_option_at_index(0).prompt
            assert isinstance(prompt, Text) and prompt.plain == row and not prompt.spans
            status = app.query_one('#fleet-status', Static).render()
            assert '1 stale, 2 malformed' in str(status)
            await pilot.press('enter')
        assert app.return_value is run
        empty = FleetView((), view.malformed_entries, view.stale_entries)
        output = io.StringIO()
        class NoRead(io.StringIO):
            def readline(self, *args):
                raise AssertionError('empty fleet must not wait for selection')
        assert run_plain_fleet(empty, input_stream=NoRead(), output_stream=output) is None
        assert 'No live runs available' in output.getvalue()
        assert '1 stale, 2 malformed' in output.getvalue()
        app = FleetApp(empty)
        async with app.run_test() as pilot:
            assert app.query_one(OptionList).option_count == 0
            assert 'No live runs available' in str(app.query_one('#fleet-status', Static).render())
            await pilot.press('enter', 'q')
        assert app.return_value is None
    print('Actual Textual/plain selectors: hostile text literal and control-free, gaps visible, exact identity selected, empty fleet safe')


asyncio.run(main())
