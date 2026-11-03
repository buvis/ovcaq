# Task13 build evidence

Native OpenAI gpt-6.1-sol/medium, logical sonnet; pipeline lean. Test-only source exception skips Tess/red; self-deslop and Pat skipped:test-only. style_gate:fixed:c094be57da57d4899b174a1071936926fa082ef5; split_hygiene:clean. No completion-review approval.

## Worker report

Task: P07-T06ab, descendant TERM/KILL and CLI-backed workflow slice.
Status: implemented; narrow gate failed during workflow harness setup, corrected afterward but not rerun (one-run mandate).
Model: native OpenAI gpt-6.1-sol, medium, logicalsonnet; no external agent CLI.
Scope: only paired fake/test implementation plus this requested report. No production changes, real launcher/workflow runs, durable repo state edits, plugin mutations, or commits.
Preserved: all 36 existing cases and original replay fixtures/provenance; argv/probe/failure tests unchanged.
Added: descendant-term and descendant-kill scenarios, actual isolated process groups, bounded TERM/KILL waits and child reaping; fake workflow scenario invokes installed ovcaq CLI in temporary repository, selects only during build, commits exactly one phase-complete per launch using expected revision, and emits command/phase evidence.
Verification: UV_CACHE_DIR=/private/tmp/ovcaq-uv-cache; uv run pytest tests/drivers/test_codex_fake.py -q --tb=line; timeout300; run once.
Result: exit1, 38 passed, 1 failed, 2 pytest temporary-directory cleanup warnings, 11.43s. Failure was protected work.prd setup via state set; appended public --unsafe flag afterward. Workflow remaining assertions are unverified. No rerun.
Budget: complete prompt plus scoped inspections conservatively below60KB, under100KB total/80KB additional limits. No broad source reads.
Style: new functions4-44 lines; files178 and289 lines. Existing main was74 lines and remains a preexisting style failure, now79 due only new scenario dispatches; no unrelated refactor.
Signal cleanup: normal TERM exits descendant and parent reaps it; stubborn mode proves group TERM ignored, then kills/reaps descendant before group KILL terminates parent to avoid orphaning. Finally cleanup bounded.
Remaining: next sequential child owns remaining scenario families and further narrow gate; shared OwnedProcess conformance remains task8.
ASSUMPTIONS:
- work.prd setup in the temporary harness uses the public CLI --unsafe flag because the narrow run rejected ordinary state set.
- workflow select result.prd is the selected PRD basename (assertion pending verification).
FILES_TOUCHED:
tests/fixtures/codex/v1/fake_codex.py
tests/drivers/test_codex_fake.py
docs/dev/tmp/replan09-task13-ivan-report.txt


## Root verification

uv run pytest tests/drivers/test_codex_fake.py -q --tb=line
.......................................                                  [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-b485c131-3cc9-409e-984e-d0d95ae684d3
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-b485c131-3cc9-409e-984e-d0d95ae684d3'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-32207359-8a18-4fb7-bf6a-0c6c15624c31
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-32207359-8a18-4fb7-bf6a-0c6c15624c31'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
39 passed, 2 warnings in 11.86s
exit_code=0