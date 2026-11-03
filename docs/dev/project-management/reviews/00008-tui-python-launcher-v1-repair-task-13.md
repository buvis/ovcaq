# PRD 00008 recovery task 13

Prerequisite split from task 1's real-adapter regression. The identity fix
advanced the regression to a missing normalized-description label. Task 13
adds only that existing-field fallback, preserving explicit labels, sanitization,
and exact identity filtering. Base `28bf789`, fix `cfb4c34`.

Micro eligibility: one MEDIUM finding in one clean production file; computed
gate true. Commit changes two files including mandatory CHANGELOG, +3 net lines.
No Tess/Devon dispatch or test weakening. Style clean; no test-file split check.
Self-deslop skipped as trivial.

Verification: `uv run pytest -q --tb=line tests/integration/test_native_telemetry_identity.py`
exited 0: **6 passed, 2 warnings in 0.27s**. Warnings concern pytest temporary
directory cleanup. The run required approved subprocess/filesystem access.

External Pat: Anthropic `claude-sonnet-5-5`, confirmed by the native transcript.
Session `aebaa0c0-63f9-4353-ba01-5dca7af695b2`; dispatch `16ce1def`;
installed `sonnet-run.sh -t ''`, no permission bypass, approved network access.
Raw reviewer output follows verbatim; parser returned no findings and resolved C12.

CLOSURE | resolved | C12 🟡 ProjectObserver ignores the normalized lane description field, so real adapter activity shows only its lane ID despite retaining a human-readable description | The added `if label is None: label = _payload_text(event, "description", gaps)` at src/ovcaq/tui/model.py:519 makes the description the label when "label" is absent, and the recorded run of the committed regression passes (6 passed).

NO FINDINGS

Assumptions: none. Full package gates and fresh completion review remain due.
