# Operator authorization — cycle 4 recovery, 2026-10-13

The operator requested decisions one by one and replied "I agree" to each:

1. R1: Change the protocol wording from "HTTP, status or error-code context" to "HTTP, status or error context", with examples.
2. R2: Remove the redundant HTTP-group alternatives already covered by the top-level error and status alternatives, preserving behavior.
3. R5: Replace the numeric-classification changelog entry with: **drivers**: prevent ordinary counts such as "processed 401 files" from triggering Codex failure handling; numeric failure codes require an HTTP, status or error label.
4. Raise rework_cap from 4 to 5 for one fresh complete Alice/Blake/Bob review after these repairs. Every existing review gate remains required.
5. Permit normal PRD finalization if cycle 5 passes every gate with no new unresolved actionable findings. New actionable findings require an operator decision.

This supersedes the prior prohibition on these three repairs and this single cap increase only. All settled deferrals remain settled. No broader grammar, additional repair loop, cap above 5, or finalization against old receipts is authorized.

Codex remains coordinator. Delegate substantive edits using the host's explicit native model/effort mapping. Preserve all 26 completed tasks, previous raw reviews, receipts, verification evidence, implementation provenance and batch progress. Use the existing state CLI as the sole writer. Complete the repair work and its required verification, then advance cycle 4 to 5 with the canonical rework transition and END the work session. The full review and any subsequent finalization run in separate fresh sessions.

Recovery detail: cycle 4 previously called review-close with an empty findings array while awaiting this decision. Its applied-review-batch marker therefore blocks the newly approved findings as "already applied", although no D4 tasks exist. The original state and empty input remain preserved. Remove only that empty batch's marker through statectl, then re-close the canonical review with the three approved findings; the existing grouper creates the tasks atomically. Preserve all earlier batch markers and reviewer results.
