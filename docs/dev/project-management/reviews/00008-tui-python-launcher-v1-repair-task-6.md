# PRD 00008 recovery task 6

JSON run now requires explicit --no-tui regardless of TTY state; non-JSON non-TTY runs retain foreground dispatch. Viewer imports occur inside the interactive attachment/resume entrypoints. Fresh CLI import, initialization and state show load no TUI, Textual or Rich modules. No timing claim is made.

Micro lane mechanically eligible: two non-CRITICAL findings in one production file, clean at claim. Coordinator made the edit; no Tess/Devon/Ivan dispatch or test commit/red-check, as the source micro procedure requires. Net6 lines over cli.py and CHANGELOG.md, below the30-line/two-file ceiling. Baseff7a6922c4207074a266d0b9d326bb91318a0376; final92e15b3a097cce6e7e044dd5c57678ff29531e4c. Self-deslop skipped:trivial, style clean, split hygiene skipped:no-tests, reflow clean. Micro routing bypasses helper implementation dispatch; no Qwen/Gemini probe or fallback claim.

Committed verification: uv run pytest -q --tb=line tests/state/test_cli.py -k 'normalizes_argparse or accepts_only_declared or json_failures': exit0,15 passed,39 deselected,2 pytest cleanup warnings in0.13s. Fresh-process scratch harness verified11 routing cases (JSON reject/explicit foreground across all4 TTY pairs and3 non-JSON non-TTY pairs), exact usage error/streams, no forbidden dispatch, and module isolation after import/init/state show. Harness stubs only foreground execution at the public CLI dispatch I/O boundary; it does not establish actual supervisor launch behavior. Two initial harness mistakes (assuming wrapped JSON reads, comparing un-resolved temporary paths) were corrected from the existing contracts without production changes. All logs preserved. No retained test changes; the complete final harness and exact command evidence follow below.

Known phase-end regression work: pre-existing tests monkeypatch the former cli.attach alias, and a pre-existing JSON foreground case expects missing --no-tui to succeed. Those tests have not been run or silently weakened here; actual failures must be reconciled with the corrected public contract at the mandated full-suite gate. The task5 integration test's viewer I/O patch uses the former alias as well. No compatibility alias was added solely to satisfy internal monkeypatches.

Patf3d4fac8 used tool-free Claude via the guarded use-sonnet wrapper with approved network. Prompt15,234bytes; sessionc2407cc6-f49d-4c16-a1ba-3e85cccffaac, actualclaude-sonnet-5-5 confirmed from model metadata. Output parser passed: F05 and F23 resolved, NO FINDINGS. This is per-task review only; completion review remains a fresh-session obligation.

## Raw task review

CLOSURE | resolved | F05 "JSON `run` without `--no-tui` is silently dispatched as a foreground run, although the CLI contract requires JSON mode to reject it unless `--no-tui` is explicit" | The diff adds `if args.command == "run" and args.json and not args.no_tui: raise CommandError(ErrorCode.USAGE, "JSON run requires --no-tui")`. The harness shows a usage error in all 4 TTY combinations, with no foreground call. `run --no-tui` and non-JSON non-TTY `run` still go foreground.

CLOSURE | resolved | F23 "`cli.py` imports `ovcaq.tui.app` at module top, and that module imports Textual and Rich at import time" | The top-level `from ovcaq.tui.app import RunControlService, attach` is removed. The imports now sit inside `_attach_view` and `_resume_and_attach`. The harness asserts that no `rich`, `textual` or `ovcaq.tui` modules are loaded after a fresh import, `init` and `state show`.

NO FINDINGS


## Recorded verification and scratch harness

{
  "command": [
    "uv",
    "run",
    "pytest",
    "-q",
    "--tb=line",
    "tests/state/test_cli.py",
    "-k",
    "normalizes_argparse or accepts_only_declared or json_failures"
  ],
  "exit": 0,
  "timeout_seconds": 300
}
...............                                                          [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-fead2d36-bfd2-4683-8a30-7cc31bd19316
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-fead2d36-bfd2-4683-8a30-7cc31bd19316'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-810b9598-50f3-4af1-9f48-efae262609a6
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-810b9598-50f3-4af1-9f48-efae262609a6'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
15 passed, 39 deselected, 2 warnings in 0.13s

{
  "command": [
    "uv",
    "run",
    "python",
    "docs/dev/tmp/verify_r6.py"
  ],
  "exit": 0,
  "timeout_seconds": 300
}
11 CLI routing cases passed; fresh import, init and state show loaded no TUI/Rich/Textual modules

Verification harness (scratch only; foreground dispatch I/O stub, actual public CLI):
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

import ovcaq.cli as cli


class Stream(io.StringIO):
    def __init__(self, tty):
        super().__init__()
        self.tty = tty

    def isatty(self):
        return self.tty


def invoke(argv, stdin_tty=False, stdout_tty=False):
    out, err = Stream(stdout_tty), io.StringIO()
    with patch.object(sys, 'stdin', Stream(stdin_tty)), redirect_stdout(out), redirect_stderr(err):
        result = cli.main(argv)
    return result, out.getvalue(), err.getvalue()


def no_viewer_modules():
    loaded = [m for m in sys.modules if m.split('.')[0] in ('rich', 'textual') or m.startswith('ovcaq.tui')]
    assert not loaded, loaded


no_viewer_modules()
with tempfile.TemporaryDirectory(prefix='ovcaq-r6-') as directory:
    root = Path(directory).resolve()
    os.environ['XDG_STATE_HOME'] = str(root / 'xdg-state')
    os.environ['XDG_CONFIG_HOME'] = str(root / 'xdg-config')
    prefix = ['--root', str(root), '--json']
    assert invoke(prefix + ['init'])[0] == 0
    result, out, err = invoke(prefix + ['state', 'show'])
    assert result == 0 and json.loads(out)['revision'] == 0 and not err
    no_viewer_modules()
    calls = []

    def foreground(args, selected, **kwargs):
        calls.append((selected, args.no_tui))
        return {'decision': 'probe'}, None, False, 9

    cases = 0
    with patch.object(cli, 'dispatch_supervisor', foreground):
        for stdin_tty, stdout_tty in [(False, False), (False, True), (True, False), (True, True)]:
            calls.clear()
            result, out, err = invoke(prefix + ['run'], stdin_tty, stdout_tty)
            assert result == 1 and not out and calls == []
            failure = json.loads(err)
            assert failure['ok'] is False and failure['error']['code'] == 'usage'
            assert '--no-tui' in failure['error']['message']
            cases += 1
            calls.clear()
            result, out, err = invoke(prefix + ['run', '--no-tui'], stdin_tty, stdout_tty)
            assert result == 9 and not err and calls == [(root, True)], (result, err, calls, root)
            assert json.loads(out) == {'decision': 'probe'}
            cases += 1
        for stdin_tty, stdout_tty in [(False, False), (False, True), (True, False)]:
            calls.clear()
            result, _, err = invoke(['--root', str(root), 'run'], stdin_tty, stdout_tty)
            assert result == 9 and not err and calls == [(root, False)]
            cases += 1
    no_viewer_modules()
print(f'{cases} CLI routing cases passed; fresh import, init and state show loaded no TUI/Rich/Textual modules')

Micro lane: no new retained tests; existing CLI argument/error tests passed. Two earlier scratch-harness failures were corrected to match actual raw JSON reads and resolved physical roots, without production changes.
