# PRD 00054 review permission recovery

The 2026-10-15 session stopped before optional Carl dispatch because automatic
approval denied exporting repository context to Gemini/Copilot. The helper did
not run. This was not a backend failure or an exit-4 availability result.

On 2026-10-16 the operator requested interactive recovery. Their standing
authorization in `~/.claude/AGENTS.md` says: "A routine reversible pause may be
resolved under this standing authorization; an irreversible-action pause may
not." It also requires preserving every required review lens and test gate.

Recovery decision: skip optional Carl for batch `202610092123`, using the
existing batch inactive-reviewer mechanism. This is an autonomous, reversible
roster decision under that standing authorization, not new permission to export
repository context and not a claim that the operator answered the prior prompt.
Keep the approval denial intact. Record the skip's policy origin in
`batch.unavailable_reviewer_details.carl`; describe it as a policy skip rather
than permanent backend unavailability in subsequent reviews. A later explicit
operator authorization can remove the batch skip at a session boundary. The
skip expires with this batch.

Verified before recovery:

- `driver.py review-route` requires Anthropic for all three review lenses.
- The host's `adapter.bob_gap` validator accepted Alice, Blake, and Bob receipts:
  matching PRD, cycle, repository and implementation fingerprint; unchanged
  output and raw JSONL hashes; successful provider results; complete rubrics.
- State schema is valid. Cycle remains 1, rework cap remains 2, and all three
  original tasks remain completed. Implementation attempts and the audit remain
  unchanged.

Retain the full review evidence in
`00054-activity-projection-corrections-v1-review-1-permission-pause.md`. It is a
draft, not a canonical completed review. The fresh review session must finish
consolidation, adjudication and the decision gate before any rework. Reuse the
validated required reviewer outputs for this same implementation snapshot;
validate them again before reuse and rerun required lenses if provenance has
changed. Later cycles still require every full review lens.

No review finding is waived here. In particular, retain Blake's two HIGH
findings, full-suite result of 7249 passed / 2 failed, isolated rerun of 14 passed,
and the separate build result of 7251 passed / 0 failed. The next review session
owns adjudication and any required verification or repair. No cap increase,
convergence, PRD move or production edit is part of this recovery.

Resume through the installed state CLI: restore `phase` and `next_phase` to
`review`, then remove the resolved permission pause. The transition table has
no paused-to-review outcome, so use the recovery procedure's field mutations,
with the pause reason removed last. Write the contract card, session brief and
handoff before ending the recovery session; the operator then runs `autocodex`.
