# PRD 00008 recovery task 1

Base `e013397`, tests `0764b91`, identity/typing implementation `28bf789`,
separately reviewed prerequisite `cfb4c34`. Native Tess and Ivan ran isolated
at logical sonnet / actual OpenAI `gpt-5.6-sol`. Tess used two dispatches
(initial plus helper-size correction), no Devon at this tier. Tests were
committed before implementation. The expected red was 1 failed/5 passed on
adapter-owned run ID. After implementation, the same test exposed the separate
description projection issue and task 1 was interrupted while task 13 closed it.

The unchanged regression then passed all six cases at `cfb4c34`; that same-HEAD
coordinator result was reused on continuation. Command: `uv run pytest -q
--tb=line tests/integration/test_native_telemetry_identity.py`, exit 0,
6 passed, 2 pytest temporary-cleanup warnings. Sandbox-denied cache and ps runs
are retained in scratch evidence; approved retry produced the behavioral result.
Strict package mypy remains due at the final work-phase gate.

Four test-author quality checks passed; computed tautology check had no findings.
Self-deslop skipped for 17 net implementation lines. Style and split hygiene
passed. Raw bytes and native IDs remain unchanged; canonical run/session identity
binds returned and persisted normalized observations only when explicitly owned.

Pat ran externally via the installed tool-free `sonnet-run.sh`, approved network,
no permission bypass. Actual Anthropic model `claude-sonnet-5-5` verified from
native session `9dd367a9-e572-414d-8c08-b9ddb59decc9`. Initial render exceeded the
50K prompt limit (52,462 bytes) and was never dispatched. One permitted trim
removed unrelated prior runtime changes and broad source-phase prose, retaining
all three findings and concrete prerequisite diffs; dispatched prompt 46,326
bytes, dispatch `34797536`. Parser accepted all three resolved closures and two
LOW findings. Raw reviewer output follows verbatim.

CLOSURE | resolved | C11 🟡 SessionEvidenceStatus construction uses a variable-length positional bool list together with raw_only, causing strict typing to reject its field assignment | `session.py` now builds `SessionEvidenceStatus(raw=present[0], normalized=present[1], summary=present[2], raw_only=...)` with explicit fields. I could not run mypy here, so strict-typing acceptance rests on the diff alone.

CLOSURE | resolved | F01 🟠 ProjectObserver follows runtime `events.jsonl`, but supervisors write normalized observations only to each session's `normalized.jsonl`; real TUI polls therefore never receive provider, activity-lane, or live-usage events | The prerequisite diff points the `JsonlFollower` at `sessions/<id>/normalized.jsonl`. This task adds `replace(observation, run_id=self._run_id, session_id=self._session_id)` in `RawFirstDecoder`, so the observer's exact `(run_id, session_id)` filter accepts real adapter output. `Supervisor` passes `session_id=session_id`. The integration test checks provider, lane and usage from real Claude decode, and checks that foreign-identity rows are filtered out.

CLOSURE | resolved | F19 🟡 The raw-file degradation path never fires in production. `observe_run().active_session_id` comes from run.json, whose `session_id` the supervisor sets to the run_id... | The prerequisite diff republishes run metadata with `replace(self._metadata, session_id=session_id)` for each real session. The observer's `session_id` therefore matches the real session directory. The `evidence_presence...` test covers the raw-only and empty-normalized cases.

LOW | src/ovcaq/events/tail.py:66 | `_bind_identity` duplicates `session_id is not None`, so it is a second piece of state that can drift from the first. | Drop the flag and test `self._session_id is not None` in the binding branch.

LOW | tests/integration/test_native_telemetry_identity.py:177 | `LiveClaudeDriver.summarize` normalizes `tool_uses` and advances state inside the driver, so the test does not prove the independent summary publication path. The task text already notes this. | Add a later test that runs the real `summarize` unpatched, or name the override in a comment.

Coordinator disposition: removing the fixed ownership flag would change the
standalone decoder after it learns a native session ID, so that LOW suggestion
is rejected. The summary-publication coverage limitation remains explicit in
the assumption ledger. No fresh completion-review approval is claimed.
