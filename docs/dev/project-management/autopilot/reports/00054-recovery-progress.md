# Interactive verification recovery

## Recovery completed, 2026-10-17

Operator's host suite XML (`00054-recovery-pytest.xml`) records 7,257 tests, 7,256 passed, one failure, no errors/skips in 268.899 seconds. All six new regression cases and all existing viewer cases passed. Sole failure: `test_sdist_contains_only_allowlisted_committed_inputs`; sdist contained the new test file while `git ls-files` omitted it because recovery intentionally left it untracked pending verification. This was a tracking precondition failure, not a viewer regression. No assertions or packaging allowlist were changed.

Committed the prepared source and tests as `00b2fdf9f2c56dac0bd32fb7f12304fc33571274`. Re-ran only that failing packaging test: 1 passed, exit 0, two existing pytest cleanup warnings; see `00054-recovery-packaging-output.txt`. No additional production/test edit followed the operator suite. The step-7 recovery procedure reruns failing checks only; full-suite counts at the final commit are null in last-verification, so fresh cycle-2 review must obtain its own suite result. Do not represent the targeted rerun as a new 7,257/0 suite.

Task 4 attempt 3 attributes the viewer recovery source/test contribution to the observed native worker model/session below; earlier attempts and cycle-1 reviewed snapshot remain preserved. Final-verification regression repair requires no extra Pat dispatch. Existing style/split gates and static verification passed. No fail-first functional claim: the earlier regression attempts were setup denials. No additional queued cycle-1 verification checks exist. Recovery resumes the existing rework handoff only; no completion reviewers ran here, no convergence is claimed and cap remains 2.

The sections below are the chronological preparation/blocker record; their pending/uncommitted statements were superseded by this recovery completion.

Cycle 1 / cap 2 retained. No phase-done, review, cycle increment, or review waiver. Existing reviewed implementation snapshot and receipts remain untouched.

## Diagnosis and prepared repair

Mixed lifecycle samples in `_selected_state` and `observe_selected_run` can invalidate ordinary supervisor cleanup as `state=None, ended=True`. ProjectObserver freezes that uncertain terminal frame; viewers report failed instead of completed. A second edge can discard the selected session cache and lose final telemetry.

Prepared changes (uncommitted pending verification): sample selected process death before metadata; bounded re-sample when cleanup overtakes identity; defer delivery of an invalidated live-to-terminal frame only when the following snapshot proves valid same-selected-run terminal attestation and batch identity. Retain session cache only for nonterminal invalid samples with exact selected run/process identity. Replacement, missing attestation, or digest mismatch remain fail-closed.

New `tests/integration/test_observer_exit_during_poll.py` covers four forced real-supervisor exit boundaries (identity, run, state, evidence), final frame/telemetry retention and freezing, plus two missing/damaged terminal attestation cases. No assertions weakened, sleeps added, or blanket retry loop introduced.

Logical sonnet, actual OpenAI gpt-6.1-sol / medium, isolated native worker session 01a146a4-de42-7031-a9b3-9b006f25fca2. Raw model metadata retained byte-for-byte at `autocodex-sessions/00054-recovery-viewer-model-metadata.jsonl`. Independent Anthropic review route remains available; completion review must occur in a fresh session. Attribute these recovery source/test contributions when completing task 4 and rebuilding cycle-2 model evidence; do not overwrite the cycle-1 reviewed snapshot.

## Verification and external blocker

uv sync --all-groups, repository-wide ruff check, ruff format --check, mypy src/ovcaq and uv build passed. Style-limit and split-hygiene gates passed on the prepared recovery diff.

Two attempted regression invocations (ordinary and tool-escalated) failed at fixture setup because the outer macOS Seatbelt denied ps. They are infrastructure failures, NOT confirmed red regression results. Raw logs: `00054-recovery-viewer-red.txt` and `00054-recovery-viewer-red-approved.txt` (the latter name denotes requested tool escalation, which did not escape the outer profile). No functional green or fail-first claim.

Warrant d86ed27ba485f83ddeb6b4443ca5a5b2 was refused because UV_CACHE_DIR is outside allowed_env. No test ran through that warrant. Replacement warrant f20d90da5ac008469f9ec08b440cbf82 requests the same full pytest run using uv's supported cache CLI option, with no environment override. Exact command: `/Users/bob/.local/bin/mise exec -- uv --cache-dir /private/tmp/ovcaq-recovery-uv-cache run pytest -q --tb=short --junitxml=docs/dev/project-management/autopilot/reports/00054-recovery-pytest.xml`, project cwd. Approve on the host with `~/bin/warrant approve f20d90da5ac008469f9ec08b440cbf82`.

## Resume

Read warrant result and XML; do not launch another blanket suite while the warrant is pending/running. If functional tests fail, diagnose the exact failure; do not treat setup denial as product red. After genuine verification passes, commit the recovery source/tests, record task-4 contribution/attempt and honest last-verification at that HEAD, complete task 4 via state CLI, clear verification pause and restore review phase via state CLI. Then phase-done --outcome rework exactly once to cycle 2, write card/brief/leave evidence and record store, STOP for fresh independent three-lens cycle-2 review. Never advance from paused or claim convergence from this recovery.

ASSUMPTIONS: none.

## Warrant executable-policy blocker

Replacement warrant f20d90da5ac008469f9ec08b440cbf82 was also refused: /Users/bob/.local/bin/mise is outside trusted_exe_roots. No suite ran. The virtualenv Python resolves to /Users/bob/.local/share/uv/python/cpython-3.13.16-macos-aarch64-none/bin/python3.13; its warrant trust is unknown. Do not wrap the refused launcher in a trusted shell or alter private warrant policy. Operator must identify a permitted compatible Python executable before another request. Recovery edits remain prepared and unverified; cycle/cap unchanged.
