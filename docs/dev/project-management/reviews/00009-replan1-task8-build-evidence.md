# Task8 build evidence

Native OpenAI gpt-6.1-sol/medium, logical sonnet; pipeline lean. Test-only source exception skips Tess/red; self-deslop and Pat skipped:test-only. style_gate:fixed:4e564e96c670d8557c0a4df993d40d7285cb02e6; split_hygiene:clean. No completion-review approval.

## Worker report

P07-T06b / Task 8 implementor report

Changed only the three named test paths; no production, fixture, state, plugin or commit edits.
All existing Claude assertions remain. Existing process tests now run both built-in adapters through actual launch/decode/summary edge injection. Shared conformance covers exact argv/default prompt, cache split 120 total/100 read/0 write/30 output -> 20 uncached, cumulative replay, terminal nonzero, failure classification/reset/no reset, success prose, raw-before-decode durability/redaction/private permissions, real TERM/KILL, parent exit, descendant cleanup and independent sentinel survival. Shared supervisor process tests preserve timeout/signal/duplicate ownership evidence assertions with isolated HOME/XDG roots and closed agent stdin.

One exact Verify invoked, 300-second subprocess timeout, UV_CACHE_DIR=/tmp/ovcaq-task8-uv-cache:
uv run pytest tests/drivers/test_conformance.py tests/drivers/test_claude_process.py tests/runtime/test_supervisor_process.py -q --tb=line
Initial result: 26 passed, 22 failed, exit 1, 0.43s.
Sixteen failures were sandbox PermissionError spawning ps; three were incomplete Codex default-prompt literal; three were Claude unsupported diagnostic edge literals. Corrected exact prompt and native diagnostic edge literals. No rerun by implementor; root will run authorized elevated verification. Initial evidence: /tmp/ovcaq-task8-verify.txt. Root elevated gate then reported 47 passed/1 failed; the remaining Codex process oracle incorrectly omitted the mandated trailing cache-write uncertainty observation. Corrected to the exact full 10-event sequence and exact gap reason; no implementor rerun. Root evidence: docs/dev/tmp/replan09-task8-final-narrow.txt.
Ruff check passed on all three paths; formatter applied only named test paths.
Decision policy belongs to the explicitly sequenced next task, per root instruction; decision.py not read.
Input below 100K tokens; no full supervisor/config/store reads. No external CLI model execution.

ASSUMPTIONS:
Claude process-group scenarios are supplied as harmless inline Python at the driver edge because the read-only fake_claude executable supports only healthy replay.
FILES_TOUCHED:
tests/drivers/test_conformance.py
tests/drivers/test_claude_process.py
tests/runtime/test_supervisor_process.py

Rootcorrection: report concurrentdefaultprompt claim is incorrect; prefixalreadycommitted beforedispatch. Supplied edgeoracles corrected; trailinggap exactsequence retained; rootverification separatelyrecorded.


## Root verification

uv run pytest tests/drivers/test_conformance.py tests/drivers/test_claude_process.py tests/runtime/test_supervisor_process.py -q --tb=line
................................................                         [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-964061d3-0b80-421d-9e3a-1f5e0bb124b3
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-964061d3-0b80-421d-9e3a-1f5e0bb124b3'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-2a7696db-e5ba-4620-acd5-335fa051e6b7
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-2a7696db-e5ba-4620-acd5-335fa051e6b7'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
48 passed, 2 warnings in 14.40s
exit_code=0